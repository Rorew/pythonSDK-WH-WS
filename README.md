### 关于SDK
1.  由官方最新websocket Python sdk魔改而来
2.  回调接口默认校验qq官方平台header, 其他请求将被拒绝, 默认关闭fastapi doc
3.  如需添加限流器或其他中间件, 请修改以下方法: ymbotpy.gateway.init_fastapi
4.  现代化QQ机器人框架平台: https://www.siriusbot.cn/
5.  镜芯API: https://api2.wer.plus
6.  镜芯科技官方交流群: 376957298
7.  更多细节查阅main.py

### 安装

```bash
git clone https://github.com/HG-ha/ym-qq-botpy.git
pip install -r ym-qq-botpy/ymbotpy/requirements.txt
```