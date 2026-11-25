from fastapi import APIRouter, HTTPException, Depends
from lessonai.services.visual_requirements import confirm_requirement, checked_requirement, VisualError
from lessonai.services.geometry_scene import build_scene

from lessonai.core.ownership import require_owner

router = APIRouter(prefix="/api/v1/visuals", tags=["Visual requirements"])


@router.post("/confirm")
def confirm(data: dict, owner=Depends(require_owner)):
    try:
        return confirm_requirement(data)
    except (ValueError, KeyError, TypeError) as error:
        raise HTTPException(422, detail={"code": "visual_invalid", "message": str(error)}) from error


@router.post("/scene")
def scene(spec: dict):
    try:
        checked_requirement(spec)
        return build_scene(spec)
    except VisualError as error:
        raise HTTPException(409, detail={"code": error.code, "message": str(error)}) from error
