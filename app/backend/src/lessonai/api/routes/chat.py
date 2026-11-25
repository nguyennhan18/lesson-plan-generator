from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from lessonai.core.ownership import require_owner
from lessonai.schemas.slide_schema import SlideDeckSchema
from lessonai.services import copilot
router=APIRouter(prefix='/api/v1/chat',tags=['Chat Co-pilot'])

@router.post('/sessions')
def create_session(data: dict, owner=Depends(require_owner)):
    try:
        deck=SlideDeckSchema.model_validate(data['slide_deck'])
    except (KeyError, ValidationError) as error:
        raise HTTPException(422, detail='Bộ slide không hợp lệ') from error
    return {'session_id':copilot.new_session(owner,deck)}

@router.post('/interact')
def interact(data:dict,owner=Depends(require_owner)):
    try:
        return copilot.interact(owner,data)
    except HTTPException:
        raise
    except (KeyError,ValidationError) as error:
        raise HTTPException(422,detail='Dữ liệu hội thoại không hợp lệ') from error
    except Exception as error:
        raise HTTPException(503,detail={'code':'chat_unavailable','message':'Không nhận được phản hồi AI. Bản soạn được giữ nguyên.'}) from error

@router.get('/history/{session_id}')
def history(session_id:str,owner=Depends(require_owner)):
    return {'history':copilot.history(owner,session_id)}

@router.delete('/session/{session_id}')
def reset(session_id:str,owner=Depends(require_owner)):
    copilot.reset(owner,session_id)
    return {'cleared':True}

@router.post('/apply-patch')
def apply(data:dict,owner=Depends(require_owner)):
    try:
        return {'slide_deck':copilot.apply(owner,data),'success':True}
    except HTTPException:
        raise
    except (KeyError,ValueError) as error:
        raise HTTPException(422,detail=str(error)) from error
