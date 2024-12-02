# -*- coding: utf-8 -*-
'''
Author: 一铭
Github: https://github.com/HG-ha

欢迎加入镜芯科技官方QQ: 376957298
'''
import ymbotpy
from ymbotpy.message import DirectMessage, Message, GroupMessage, C2CMessage

class MyClient(ymbotpy.WebHookClient):
    async def on_at_message_create(self, message: Message):
        """频道内@"""
        await message.reply(content=f"机器人{self.robot.name}收到你的@消息了: {message.content}")

    async def on_group_add_robot(self, message: Message):
        """添加到群聊"""
        pass

    async def on_guild_create(self, message: Message):
        """添加到频道"""
        pass

    async def on_direct_message_create(self, message: DirectMessage):
        """频道私聊"""
        pass

    async def on_group_at_message_create(self, message: GroupMessage):
        """群消息"""
        pass
    
    async def on_c2c_message_create(self, message: C2CMessage):
        """qq私聊"""
        pass

if __name__ == "__main__":
    BOT_APPID = 'botid'
    BOT_SECRET = 'secert'
    client = MyClient()

    # 无代理, 直接内部绑定域名，需要配置ssl
    # client.run(appid=BOT_APPID,secret=BOT_SECRET,system_log=True,
    #            ssl_keyfile='ssl/private.key',ssl_certfile='ssl/public.crt')
    
    # 通过nginx等反向代理时，无需配置ssl证书
    client.run(appid=BOT_APPID,secret=BOT_SECRET,port=80,system_log=True)

    '''
    魔改自官方websocket sdk
    
    回调接口默认校验qq官方平台header, 其他请求将被拒绝, 默认关闭fastapi doc
    如需添加限流器或其他中间件, 请修改以下方法: ymbotpy.gateway.init_fastapi

    
    由于调用方式的变化，已无需注册监听事件，在管理端进行控制
    未注册的方法将不会进行处理
    其他API以及各种数据类型修改依然可按照官方文档迭代


    默认回调地址为: example.com/qbot/webhook
    如果想修改回调地址, 在run时增加参数: hook_route='自定义url'

    默认监听: 0.0.0.0:80, 如需配置ssl则修改port为443
    修改监听地址: host=host, port=port


    现代化QQ机器人框架平台: https://www.siriusbot.cn/
    镜芯API:               https://api2.wer.plus
    '''