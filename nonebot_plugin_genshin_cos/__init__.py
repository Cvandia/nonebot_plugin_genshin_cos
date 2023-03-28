from nonebot.adapters.onebot.v11 import MessageSegment,MessageEvent
from nonebot.plugin import on_command
from nonebot.exception import ActionFailed
from .utils import get_cos,WriteError

send_cos = on_command("原神cos",aliases={"米游社cos"},block=False,priority=5)
@send_cos.handle()
async def handle():
    img = get_cos().randow_cos_img()
    if not img:
        await send_cos.finish("未获取到图片")
    try:
        await send_cos.send(MessageSegment.image(img))
    except ActionFailed:
        await send_cos.finish("账户风控了,发送不了图片",at_sender = True)