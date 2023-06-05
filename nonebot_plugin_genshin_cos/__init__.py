from nonebot.adapters.onebot.v11 import MessageSegment, MessageEvent, Bot, Message, GroupMessageEvent
from nonebot.plugin import on_regex, PluginMetadata
from nonebot.permission import SUPERUSER
from nonebot.params import Arg, RegexGroup
from nonebot.exception import ActionFailed
from nonebot.typing import T_State
from nonebot import get_driver
from .utils import get_cos, WriteError, check_cd, GetGenShinCos, log
from nonebot.log import logger
from typing import Tuple, Any
from .config import Config
from re import I
import re
from datetime import datetime, timedelta

__plugin_meta__ = PluginMetadata(
    name="米游社cos",
    description="获取原神coser图片",
    config=Config,
    usage="原神cos",
    extra={
        "unique_name": "genshin_cos",
        "example": "保存cos:保存cos图片至本地文件",
        "author": "divandia <106718176+Cvandia@users.noreply.github.com>",
        "version": "0.1.7",
    },
)
logo = """<g>
  /$$$$$$                                /$$       /$$                  /$$$$$$                     
 /$$__  $$                              | $$      |__/                 /$$__  $$                    
| $$  \__/  /$$$$$$  /$$$$$$$   /$$$$$$$| $$$$$$$  /$$ /$$$$$$$       | $$  \__/  /$$$$$$   /$$$$$$$
| $$ /$$$$ /$$__  $$| $$__  $$ /$$_____/| $$__  $$| $$| $$__  $$      | $$       /$$__  $$ /$$_____/
| $$|_  $$| $$$$$$$$| $$  \ $$|  $$$$$$ | $$  \ $$| $$| $$  \ $$      | $$      | $$  \ $$|  $$$$$$ 
| $$  \ $$| $$_____/| $$  | $$ \____  $$| $$  | $$| $$| $$  | $$      | $$    $$| $$  | $$ \____  $$
|  $$$$$$/|  $$$$$$$| $$  | $$ /$$$$$$$/| $$  | $$| $$| $$  | $$      |  $$$$$$/|  $$$$$$/ /$$$$$$$/
 \______/  \_______/|__/  |__/|_______/ |__/  |__/|__/|__/  |__/       \______/  \______/ |_______/ 
 </g>"""
logger.opt(colors=True).info(logo)
max = Config.parse_obj(get_driver().config.dict()).cos_max
save_path = Config.parse_obj(get_driver().config.dict()).cos_path
timeout = Config.parse_obj(get_driver().config.dict()).cos_time_out
swipeTime = Config.parse_obj(get_driver().config.dict()).cos_swipe_time
user_data = {}

send_cos = on_regex(
    r"^(原神|米游社)+cos(\s)?([x|*|X]\d)?", block=False, priority=5, flags=I)
download_cos = on_regex(r"^(下载cos)|(cos保存)$", block=False,
                        permission=SUPERUSER, flags=I)
CosPlus = on_regex(r"^cosplus$", block=True, priority=5, flags=I)
cosall = on_regex(r"^xmx$", block=True, priority=5,flags=I, permission=SUPERUSER)


@cosall.handle()
async def cosa(state: T_State, bot: Bot, event: MessageEvent):
    cos = GetGenShinCos()
    state["cosa"] = cos
    await cos.start()
    imge = await cos.get_page(seconds=swipeTime)
    await cosall.send(MessageSegment.image(imge))
    img_list = await cos.get_all_img()
    await cosall.send(f"共获取到{len(img_list)}张图片")
    await cos.close()
    await send_forward_msg(bot, event, "cos", bot.self_id, msgs=[MessageSegment.image(img) for img in img_list])


@CosPlus.handle()
async def cosplus(state: T_State, bot: Bot, event: MessageEvent):
    global user_data
    out_cd, deletime, user_data = check_cd(event.user_id, user_data)
    if out_cd:
        cos = GetGenShinCos()
        state["cosPLU"] = cos
        await cos.start()
        image = await cos.get_page(seconds=swipeTime)
        try:
            await CosPlus.send(MessageSegment.image(image))
        except Exception:
            await cos.close()
            await CosPlus.finish("获取图片失败")
        state['start_time'] = datetime.now()
    else:
        await CosPlus.finish(f"你的cd时间还剩{deletime}秒")


@CosPlus.got("ablocation", prompt='请发送你要获取图片的位置，如“1 3 5”,中间用空格隔开')
async def handle(state: T_State, bot: Bot, event: MessageEvent, ablocation: Message = Arg()):
    cos = state["cosPLU"]
    if state['start_time'] + timedelta(seconds=timeout) < datetime.now():
        await cos.close()
        await CosPlus.finish("超时，不理你了(╯▔皿▔)╯")
    if not re.findall(r"\d", ablocation.extract_plain_text()):
        await CosPlus.finish("请发送正确的数字,不理你了(╯▔皿▔)╯")
    location = re.findall(r"\d+", ablocation.extract_plain_text())
    log('genshin_cos', f"用户选择了{location}")
    mode, msg_list = await cos.get_img_or_video(location)
    send_list = []
    if mode == 0:
        send_list = [MessageSegment.image(img) for img in msg_list]
    if not msg_list:
        await cos.close()
        await CosPlus.finish("获取失败")
    await cos.close()
    await send_forward_msg(bot, event, "cosplus", bot.self_id, send_list)


@download_cos.handle()
async def choose(state: T_State, bot: Bot, event: MessageEvent):
    choose_msg = ["点击下面的链接，预览选择你不需要的图片序号"]
    state['imgs'] = []
    N = 1
    for img in await get_cos().get_img_url():
        choose_msg.append(f"{N}.{img}")
        state['imgs'].append(img)
        N += 1
    try:
        await send_forward_msg(bot, event, "米游社cos", bot.self_id, choose_msg)
    except ActionFailed:
        await download_cos.finish("合并转发失败，请重试，如果多次失败，可能是账户风控了")


@download_cos.got("num", prompt="请发送你不需要的链接序号\n发送“无”为全部下载,多个序号用空格隔开")
async def down(state: T_State, num: Message = Arg()):
    got_msg = str(num)
    if got_msg == "无":
        try:
            dwn = get_cos()
            if not save_path:
                await download_cos.send("正在获取数据，未设置指定路径，默认下载到data/genshin_cos")
            else:
                await download_cos.send("正在下载cos图片至指定文件夹,请稍等……")
            num = await dwn.save_img(save_path)
            await download_cos.finish(f"保存完毕，一共保存了{num}张图片")
        except WriteError as exc:
            await download_cos.finish(f"<{exc}>")
    elif not re.findall(r"^\d", got_msg):
        await download_cos.finish("请发送正确的数字")
    else:
        num_list = re.findall(r"\d+", got_msg)
        names = await get_cos().get_img_name()
        for n in num_list:
            try:
                del state['imgs'][int(n)-1]
                del names[int(n)-1]
            except IndexError as exc:
                await download_cos.finish(f"出错了:<{exc}>\n可能是链接失效或者名称无效")
        try:
            num = await get_cos().download_urls(state['imgs'], names, save_path)
            await download_cos.finish(f"成功保存{num}张图片")
        except WriteError as exc:
            await download_cos.finish(f"出错了:<{exc}>")


max = Config.parse_obj(get_driver().config.dict()).cos_max


@send_cos.handle()
async def handle(bot: Bot, event: MessageEvent, args: Tuple[Any, ...] = RegexGroup()):
    global user_data
    args = list(args)
    img = get_cos()
    out_cd, deletime, user_data = check_cd(event.user_id, user_data)
    if out_cd:
        if not args[2]:
            await send_cos.send("获取图片中…请稍等")
            if not await img.randow_cos_img():
                await send_cos.finish("未获取到图片")
            try:
                await send_cos.send(MessageSegment.image(await img.randow_cos_img()))
            except ActionFailed:
                await send_cos.finish("账户风控了,发送不了图片", at_sender=True)
        else:
            num = int(re.sub(r"[x|*|X]", "", args[2]))
            num = num if num <= max else max
            msg_list = ['找到最新的一些cos图如下:']
            imgs = await img.get_img_url()

            for i in range(0, num):
                msg_list.append(MessageSegment.image(imgs[i]))
            await send_forward_msg(bot, event, "米游社cos", bot.self_id, msg_list)
    else:
        await send_cos.finish(f"cd冷却中，还剩{deletime}秒", at_sender=True)


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