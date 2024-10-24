# -*- coding: utf-8 -*-
import binascii
import json
from .connection import ConnectionState
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from cryptography.hazmat.primitives.asymmetric import ed25519

class BotWebHook:
    """Bot的WebHook实现

    CODE	名称	            客户端操作       描述
    0       Dispatch	        Receive         服务端进行消息推送  x
    1       Heartbeat	        Send/Receive    客户端或服务端发送心跳  x
    2       Identify	        Send            客户端发送鉴权  x
    6       Resume	            Send            客户端恢复连接  x
    7       Reconnect	        Receive         服务端通知客户端重新连接    x
    9       Invalid Session	    Receive         当identify或resume的时候，如果参数有错，服务端会返回该消息  x
    10      Hello	            Receive         当客户端与网关建立ws连接之后，网关下发的第一条消息  x
    11      Heartbeat ACK	    Receive         当发送心跳成功之后，就会收到该消息 x
    12      HTTP Callback ACK   Reply           仅用于 http 回调模式的回包，代表机器人收到了平台推送的数据()    母鸡
    13      回调地址验证         Receive         开放平台对机器人服务端进行验证
    """

    WH_DISPATCH_EVENT = 0
    WH_HEARTBEAT = 1
    WH_IDENTITY = 2
    WH_RESUME = 6
    WH_RECONNECT = 7
    WH_INVALID_SESSION = 9
    WH_HELLO = 10
    WH_HEARTBEAT_ACK = 11
    WH_CALLBACK_ACK = 12
    WH_CALLBACK_CHECK = 13

    
    def __init__(self,appid,secret,hook_route,client,system_log,botapi,loop):

        self.appid = appid
        self.secret = secret
        self.seed_bytes = secret.encode()
        self.hook_route = hook_route
        self.bot_client = client
        self.system_log= system_log
        self.botapi = botapi
        self.loop = loop

        self.conn = ConnectionState(
                self.dispatch,self.botapi
            )

    def handle_validation(self,body: dict):

        signing_key = ed25519.Ed25519PrivateKey.from_private_bytes(self.seed_bytes)

        validation_payload = body['d']
        msg = validation_payload['event_ts'] + validation_payload['plain_token']

        signature_hex = signing_key.sign(msg.encode()).hex()

        response = {
            "plain_token": validation_payload['plain_token'],
            "signature": signature_hex
        }
        return response
    
    def verify_signature(self, headers):
        signature = headers.get("x-signature-ed25519")
        if not signature:
            return False,''
        try:
            sig = binascii.unhexlify(signature)
        except (binascii.Error, TypeError):
            return False,''
        
        if len(sig) != 64 or (sig[63] & 224) != 0:
            return False,''
        
        return True,sig


    def generate_keys(self):
        seed = self.seed_bytes
        while len(seed) < 32:
            seed = (seed * 2)[:32]
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
        public_key = private_key.public_key()
        
        return public_key, private_key

    def get_signature_body(self, headers,body):
        timestamp = headers.get("x-signature-timestamp")
        if not timestamp:
            return False,''
        
        msg = timestamp.encode('utf-8') + body
       
        return True,msg


    def handle_validation_webhook(self,headers,body: dict):
        try:
            success,sig = self.verify_signature(headers)
            if not success:
                return False
            public_key, private_key = self.generate_keys()
            success, msg = self.get_signature_body(headers,body)
            if not success:
                return False
            
            public_key.verify(sig, msg)

            return True
        except:
            return False

    def dispatch(self, event, message,*args, **kwargs):
        '''
        消息分发
        '''

        method = f'on_{event}'
        try:
            coro = getattr(self.bot_client, method)
            async def runner():
                await coro(message,*args, **kwargs)
            try:
                self.loop.create_task(runner())
            except KeyboardInterrupt:
                return
        except AttributeError:
            from ymbotpy import logger
            logger.info(f"[botpy] 事件: {event} 未注册")
        

    async def init_fastapi(self):
        from ymbotpy import logger
        app = FastAPI(docs_url=None, redoc_url=None)
        @app.middleware("http")
        async def reject_unknown_routes(request: Request, call_next):
            if request.url.path != self.hook_route:
                return Response(status_code=403)  # 403 Forbidden
            response = await call_next(request)
            return response
        
        @app.api_route(self.hook_route, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
        async def qbot_callback(request: Request):
            
            if request.headers.get("x-bot-appid",'') != self.appid:
                return Response(status_code=403)
            
            if request.headers.get("user-agent",'') != "QQBot-Callback":
                return Response(status_code=403)
            
            if 'x-signature-ed25519' not in request.headers:
                return Response(status_code=403)
            
            if 'x-signature-timestamp' not in request.headers:
                return Response(status_code=403)
            
            try:
                bytes_body = await request.body()
                body = json.loads(bytes_body.decode('utf-8'))
            except Exception as e:
                logger.warning(e)
                return
            
            if self.system_log:
                logger.warning(body)

            if body.get("op") == self.WH_CALLBACK_CHECK:
                return self.handle_validation(body)
            
            if not self.handle_validation_webhook(request.headers,bytes_body):
                logger.error(f"签名校验不通过: {request.headers}")
                return Response(status_code=403)
            
            event = body.get("t").lower()
            self.conn.parsers[event](body)
            
        return app