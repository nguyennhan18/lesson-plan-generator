"""Bound request bodies before multipart spooling, including chunked requests."""
import asyncio
from starlette.responses import JSONResponse


class BodyLimitMiddleware:
    def __init__(self,app,limit=16*1024*1024):
        self.app,self.limit=app,limit

    async def __call__(self,scope,receive,send):
        if scope['type']!='http':return await self.app(scope,receive,send)
        async def reject(status,code,message):
            from uuid import uuid4
            request_id=str(uuid4())
            await JSONResponse({'detail':{'code':code,'message':message,'request_id':request_id}},status_code=status,headers={'X-Request-ID':request_id})(scope,receive,send)
        try:
            length=int(dict(scope.get('headers',[])).get(b'content-length',b'0'))
        except ValueError:return await reject(400,'invalid_content_length','Content-Length không hợp lệ')
        if length>self.limit:return await reject(413,'request_too_large','Yêu cầu vượt giới hạn 16 MiB')
        body=bytearray()
        while True:
            try:message=await asyncio.wait_for(receive(),timeout=15)
            except asyncio.TimeoutError:return await reject(408,'body_timeout','Quá thời hạn nhận yêu cầu')
            if message['type']=='http.disconnect':return
            chunk=message.get('body',b'')
            if len(body)+len(chunk)>self.limit:return await reject(413,'request_too_large','Yêu cầu vượt giới hạn 16 MiB')
            body.extend(chunk)
            if not message.get('more_body'):break
        delivered=False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered=True
                return {'type':'http.request','body':bytes(body),'more_body':False}
            return await receive()
        await self.app(scope,replay,send)
