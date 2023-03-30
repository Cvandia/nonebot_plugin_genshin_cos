from nonebot.adapters.onebot.v11 import MessageSegment,MessageEvent,Bot,Message,GroupMessageEvent
from nonebot.plugin import on_regex,PluginMetadata
from nonebot.permission import SUPERUSER
from nonebot.exception import ActionFailed
from nonebot.typing import T_State
from nonebot import get_driver
from .utils import get_cos,WriteError
from .config import Config
import re
from pathlib import Path
import requests

__plugin_meta__ = PluginMetadata(
    name = "米游社cos",
    description = "获取原神coser图片",
    config = Config,
    usage = "原神cos",
    extra = {
        "unique_name": "genshin_cos",
        "example": "保存cos:保存cos图片至本地文件",
        "author": "divandia <106718176+Cvandia@users.noreply.github.com>",
        "version": "0.1.3",
    },
)

max = Config.parse_obj(get_driver().config.dict()).cos_max
save_path = Config.parse_obj(get_driver().config.dict()).cos_path

send_cos = on_regex(r"^[原神|米游社]cos(\s)?([x|*|X]\d)?",block=False,priority=5)
download_cos = on_regex(r"^[下载cos]|[cos保存]$",block=False,permission=SUPERUSER)
@download_cos.handle()
async def down_load():
    try:
        dwn = get_cos()
        if not save_path: 
            await download_cos.send("正在获取数据，未设置指定路径，默认下载到data/genshin_cos")
        else:
            await download_cos.send("正在下载cos图片至指定文件夹,请稍等……")
        num = dwn.save_img(save_path)
        await download_cos.finish(f"保存完毕，一共保存了{num}张图片")
    except WriteError as exc:
        await download_cos.finish(f"<{exc}>")
        
    



max = Config.parse_obj(get_driver().config.dict()).cos_max

@send_cos.handle()
async def handle(bot:Bot, event:MessageEvent, state:T_State):
    args = list(state['_matched_groups'])
    img = get_cos()
    if not args[1]:
        await send_cos.send("获取图片中…请稍等")
        if not img.randow_cos_img():
            await send_cos.finish("未获取到图片")
        try:
            await send_cos.send(MessageSegment.image(img.randow_cos_img()))
        except ActionFailed:
            await send_cos.finish("账户风控了,发送不了图片",at_sender = True)
    else:
        num = int(re.sub(r"[x|*|X]","",args[1]))
        num = num if num <= max else max
        msg_list = ['找到最新的一些cos图如下:']
        imgs = img.get_img_url()
        for i in range(0,num+1):
            msg_list.append(MessageSegment.image(imgs[i])) 
        await send_forward_msg(bot,event,"米游社cos",bot.self_id,msg_list)



async def send_forward_msg(
    bot: Bot,
    event: MessageEvent,
    name: str,
    uin: str,
    msgs: list,
) -> dict:
    """调用合并转发API
    
        bot: Bot
        event: 消息事件类型
        name: 发送者昵称
        uin: 发送者账号
        msgs: 消息列表
    """
    def to_json(msg: Message):
        return {"type": "node", "data": {"name": name, "uin": uin, "content": msg}}

    messages = [to_json(msg) for msg in msgs]
    
    if isinstance(event, GroupMessageEvent):
        return await bot.call_api(
            "send_group_forward_msg", group_id=event.group_id, messages=messages
        )
    else:
        return await bot.call_api(
            "send_private_forward_msg", user_id=event.user_id, messages=messages
        )       