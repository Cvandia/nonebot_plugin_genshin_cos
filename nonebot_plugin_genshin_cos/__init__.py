from nonebot.adapters.onebot.v11 import MessageSegment,MessageEvent,Bot,Message,GroupMessageEvent
from nonebot.plugin import on_regex,PluginMetadata
from nonebot.permission import SUPERUSER
from nonebot.params import Arg
from nonebot.exception import ActionFailed
from nonebot.typing import T_State
from nonebot import get_driver
from .utils import get_cos,WriteError,check_cd
from .config import Config
from nonebot.log import logger
from re import I
import re
from pathlib import Path

__plugin_meta__ = PluginMetadata(
    name = "米游社cos",
    description = "获取原神coser图片",
    config = Config,
    usage = "原神cos",
    extra = {
        "unique_name": "genshin_cos",
        "example": "保存cos:保存cos图片至本地文件",
        "author": "divandia <106718176+Cvandia@users.noreply.github.com>",
        "version": "0.1.5",
    },
)

max = Config.parse_obj(get_driver().config.dict()).cos_max
save_path = Config.parse_obj(get_driver().config.dict()).cos_path
send_path = Path(Config.parse_obj(get_driver().config.dict()).cos_path)
user_data = {}
send_mode = 0

send_cos = on_regex(r"^(原神|米游社)+cos(\s)?([x|*|X]\d)?",block=False,priority=5,flags=I)
download_cos = on_regex(r"^(下载cos)|(cos保存)$",block=False,permission=SUPERUSER,flags=I)
switch_cos = on_regex(r"^切换(cos)?图库",block=False,priority=5,flags=I)

@switch_cos.handle()
async def switch(bot:Bot,event:GroupMessageEvent):
    global send_mode
    if send_mode == 0:
        send_mode = 1
        await switch_cos.finish("已切换到在线图库",at_sender=True)
    else:
        send_mode = 0
        await switch_cos.finish("已切换到离线图库",at_sender=True)


@download_cos.handle()
async def choose(state:T_State,bot:Bot,event:MessageEvent):
    choose_msg = ["点击下面的链接，预览选择你不需要的图片序号"]
    state['imgs'] = []
    N = 1
    for img in get_cos().get_img_url():
        choose_msg.append(f"{N}.{img}")
        state['imgs'].append(img)
        N += 1
    try:
        await send_forward_msg(bot,event,"米游社cos",bot.self_id,choose_msg)
    except ActionFailed:
        await download_cos.finish("合并转发失败，请重试，如果多次失败，可能是账户风控了")

@download_cos.got("num",prompt="请发送你不需要的链接序号\n发送“无”为全部下载,多个序号用空格隔开")
async def down(state:T_State,num:Message = Arg()):
    got_msg = str(num)
    if got_msg == "无":
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
    elif not re.findall(r"^\d",got_msg):
        await download_cos.finish("请发送正确的数字")
    else:
        num_list = re.findall(r"\d+",got_msg)
        names = get_cos().get_img_name()
        for n in num_list:
            try:
                del state['imgs'][int(n)-1]
                del names[int(n)-1]
            except IndexError as exc:
                await download_cos.finish(f"出错了:<{exc}>\n可能是链接失效或者名称无效")
        try:
            num = get_cos().download_urls(state['imgs'],names,save_path)
            await download_cos.finish(f"成功保存{num}张图片")
        except WriteError as exc:
            await download_cos.finish(f"出错了:<{exc}>")



max = Config.parse_obj(get_driver().config.dict()).cos_max

@send_cos.handle()
async def handle(bot:Bot, event:MessageEvent, state:T_State):
    global user_data,send_mode
    if send_mode == 0:
        await send_cos.send("当前模式为离线图库,正在寻找图片中")
    else:
        await send_cos.send("当前模式为在线图库,正在寻找图片中")
    args = list(state['_matched_groups'])
    img = get_cos()
    out_cd,deletime,user_data = check_cd(event.user_id,user_data)
    if out_cd:
        if not args[2]:
            if not img.randow_cos_img():
                await send_cos.finish("未获取到图片")
            try:
                await send_cos.send(MessageSegment.image(img.randow_cos_img()))
            except ActionFailed:
                await send_cos.finish("账户风控了,发送不了图片",at_sender = True)
        else:
            num = int(re.sub(r"[x|*|X]","",args[2]))
            num = num if num <= max else max
            msg_list = ['找到最新的一些cos图如下:']
            imgs = img.get_img_url()
            for i in range(0,num):
                msg_list.append(MessageSegment.image(imgs[i])) 
            await send_forward_msg(bot,event,"米游社cos",bot.self_id,msg_list)
    else:
        await send_cos.finish(f"cd冷却中，还剩{deletime}秒",at_sender = True)



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