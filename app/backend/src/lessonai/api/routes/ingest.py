import os
import asyncio
from fastapi import APIRouter,HTTPException,UploadFile,File
from lessonai.core.jobs import get_runner,JobError
from lessonai.services.uploads import MAX_FILE
router=APIRouter(prefix='/api/v1/ingest',tags=['Ingest'])

async def parse_upload(file,operation,extensions):
    try:
        filename=file.filename or ''
        if os.path.splitext(filename)[1].lower() not in extensions:
            raise HTTPException(415,detail='Định dạng tài liệu chưa được hỗ trợ')
        buffer=bytearray()
        while chunk:=await file.read(65536):
            buffer.extend(chunk)
            if len(buffer)>MAX_FILE:raise HTTPException(413,detail='Tệp vượt 12 MiB')
        if not buffer:raise HTTPException(400,detail='Tệp rỗng')
        return await asyncio.to_thread(get_runner().run,operation,{'content':bytes(buffer),'filename':filename},timeout=15)
    except JobError as error:
        status=413 if error.code=='upload_limit' else 503 if error.code=='job_busy' else 504 if error.code=='job_timeout' else 422
        raise HTTPException(status,detail={'code':error.code,'message':str(error)}) from error
    finally:
        await file.close()

@router.post('/parse-document')
async def parse_document_endpoint(file:UploadFile=File(...)):
    return await parse_upload(file,'ingest.document',{'.docx','.pptx'})

@router.post('/classify-grades')
async def classify_grades_endpoint(file:UploadFile=File(...)):
    return await parse_upload(file,'ingest.grades',{'.xlsx','.xlsm','.csv'})
