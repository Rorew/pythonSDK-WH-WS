import asyncio
from types import TracebackType
from typing import Any, Coroutine, Dict, List, Tuple, Optional, Union, Type
from . import logging
from .api import BotAPI
from .gateway import BotWebHook
from .http import BotHttp
from .robot import Robot, Token

_log = logging.get_logger()


class _LoopSentinel:
    __slots__ = ()

    def __getattr__(self, attr: str) -> None:
        raise AttributeError("无法在非异步上下文中访问循环属性")


_loop: Any = _LoopSentinel()


class Client:
    """``Client` 是一个用于与 QQ频道机器人 Websocket 和 API 交互的类。"""

    def __init__(
        self,
        timeout: int = 5,
        is_sandbox=False,
        log_config: Union[str, dict] = None,
        log_format: str = None,
        log_level: int = None,
        bot_log: Union[bool, None] = True,
        ext_handlers: Union[dict, List[dict], bool] = True,
    ):
        """
        Args:
          timeout (int): 机器人 HTTP 请求的超时时间。. Defaults to 5
          is_sandbox: 是否使用沙盒环境。. Defaults to False
          log_config: 日志配置，可以为dict或.json/.yaml文件路径，会从文件中读取(logging.config.dictConfig)。Default to None（不做更改）
          log_format: 控制台输出格式(logging.basicConfig(format=))。Default to None（不做更改）
          log_level: 控制台输出level。Default to None(不做更改),
          bot_log: bot_log: bot_log: 是否启用bot日志 True/启用 None/禁用拓展 False/禁用拓展+控制台输出
          ext_handlers: ext_handlers: 额外的handler，格式参考 logging.DEFAULT_FILE_HANDLER。Default to True(使用默认追加handler)
        """
        # TODO loop的整体梳理 @veehou
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.http: BotHttp = BotHttp(timeout=timeout, is_sandbox=is_sandbox)
        self.api: BotAPI = BotAPI(http=self.http)
        self._ws_ap: Dict = {}

        logging.configure_logging(
            config=log_config,
            _format=log_format,
            level=log_level,
            bot_log=bot_log,
            ext_handlers=ext_handlers,
        )

    async def __aenter__(self):
        _log.debug("[botpy] 机器人客户端: __aenter__")
        await self._async_setup_hook()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        _log.debug("[botpy] 机器人客户端: __aexit__")



    async def _async_setup_hook(self) -> None:
        # Called whenever the client needs to initialise asyncio objects with a running loop
        self.loop = asyncio.get_running_loop()
        self._ready = asyncio.Event()

    def run(self, *args: Any, **kwargs: Any) -> None:
        """
        机器人服务开始执行

        注意:
          这个函数必须是最后一个调用的函数，因为它是阻塞的。这意味着事件的注册或在此函数调用之后调用的任何内容在它返回之前不会执行。
          如果想获取协程对象，可以使用`start`方法执行服务, 如:
        ```
        async with Client as c:
            c.start()
        ```
        """

        async def runner():
            async with self:
                await self.start(*args, **kwargs)

        try:
            self.loop.run_until_complete(runner())
        except KeyboardInterrupt:
            return

    async def start(self, appid: str,secret: str, host: str = "0.0.0.0", port:int = 443, hook_route: str = "/qbot/webhook",
                    ssl_keyfile=None,ssl_certfile=None,system_log=True) -> Optional[Coroutine]:
        """机器人开始执行

        参数
        ------------
        appid: :class:`str`
            机器人 appid
        secret: :class:`str`
            机器人 secret
        host: :class:`str`
            服务监听地址
        port: :class:`str`
            服务监听端口
        hook_route: :class:`str`
            webhook监听路由地址
        ssl_keyfile: :class:`str`
            ssl证书秘钥，若是通过其他web反向代理过来，无需配置ssl
        ssl_keyfile: :class:`str`
            ssl证书公钥，若是通过其他web反向代理过来，无需配置ssl
        system_log: :class:`str`
            是否启用系统日志，启用时可以看到webhook接收的数据包
        """
        token = Token(appid, secret)
        user = await self.http.login(token)
        self.robot = Robot(user)

        bot_webhook = BotWebHook(appid,secret,
                                 hook_route=hook_route,
                                 client=self,
                                 system_log=system_log,
                                 botapi = self.api,
                                 loop=self.loop)
        
        app = await bot_webhook.init_fastapi()
        from uvicorn import Config, Server

        if ssl_keyfile is None or ssl_certfile is None:
            config = Config(app, host=host, port=port)
        else:
            config = Config(app, host=host, port=port,
                            ssl_keyfile=ssl_keyfile,
                            ssl_certfile=ssl_certfile)
        
        await Server(config).serve()
