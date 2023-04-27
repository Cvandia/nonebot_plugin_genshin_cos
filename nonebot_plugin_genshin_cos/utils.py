from httpx import AsyncClient
from nonebot.log import logger
from pathlib import Path
from nonebot import get_driver
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple
from .config import Config
from datetime import datetime, timedelta
from nonebot.log import logger as blog
try:
    import ujson as json
except ImportError:
    import json
import random
from playwright.async_api import async_playwright
import io
import os
import time
import re

cd = Config.parse_obj(get_driver().config.dict()).cos_cd
font_path = os.path.join(os.path.dirname(__file__), "fonts")+ "/CONSOLA.TTF"
class WriteError(Exception):
    pass


class get_cos(object):
    """获取米游社原神cos最新图片"""

    def __init__(self) -> None:
        self.url = "https://bbs-api.mihoyo.com/post/wapi/getForumPostList?forum_id=49"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
            + ' Chrome/92.0.4515.107 Safari/537.36'
        }

    async def parse(self):
        """获取网页数据

        Returns:
            dict: dict数据
        """
        img_dict_data = {}
        res = await AsyncClient().get(self.url, headers=self.headers)
        res = json.loads(res.text)
        res = res['data']['list']
        subject_name = [i['post']['subject'] for i in res]
        cover_url = [i['post']['cover'] for i in res]
        for name, url in zip(subject_name, cover_url):
            img_dict_data[name] = url
        return img_dict_data

    async def get_img_url(self) -> list:
        """获取cos图片链接列表

        Returns:
            list: 图片链接列表
        """
        data = await self.parse()
        img_list = []
        for k, v in data.items():
            img_list.append(v)
        return img_list

    async def get_img_name(self) -> list:
        """获取cos图片名称

        Returns:
            list: 图片名称列表
        """
        data = self.parse()
        name_list = []
        for k, v in data.items():
            name_list.append(k)
        return name_list

    async def save_img(self, save_path: str):
        """保存cos的图片

        Args:
            save_path: 保存的路劲

        Returns:
            int: 成功保存的数量
        """
        data = self.parse()
        path = Path(save_path)
        if not str(save_path):
            path = Path("./data/genshin_cos")
        if not path.exists():
            path.mkdir(parents=True)
            logger.warning(f"文件夹不存在，正在创建文件夹:{path}")
        N = 0
        for k, v in data.items():
            N += 1
            k = re.sub(r'^[\w-+.?？|=*]*', '', k)
            try:
                with open(path / f"{k}.jpg", 'wb') as f:
                    img = await AsyncClient().get(
                        v, headers=self.headers)  # 发送请求获取图片内容
                    f.write(img.content)
                    logger.success(f"保存成功 --> {k}")
            except Exception as exc:
                logger.error(exc)
                raise WriteError(f"出错了请查看详细报错:\n{exc}")
        return N

    def randow_cos_img(self) -> str:
        """随机cos图链接

        Returns:
            str: 图片url
        """
        return random.choice(self.get_img_url())

    async def download_urls(self, urls: list, names: list, save_path: str) -> int:
        """下载特定的图片链接

        Args:
            urls (list): 图片链接
            names (list): 图片对应名称
            save_path (str): 保存的路劲

        retrun:
            int: 返回成功保存的数量
        """
        path = Path(save_path)
        if not str(save_path):
            path = Path("./data/genshin_cos")
        if not path.exists():
            path.mkdir(parents=True)
            logger.warning(f"文件夹不存在，正在创建文件夹:{path}")
        N = 0
        for url, name in zip(urls, names):
            N += 1
            name = re.sub(r'^[\w-+.?？|=*]*', '', name)
            try:
                with open(path / f"{name}.jpg", 'wb') as f:
                    img = await AsyncClient().get(url, headers=self.headers)
                    f.write(img.content)
                    logger.success(f"保存成功 --> {name}")
            except Exception as exc:
                raise WriteError(exc)
        return N


class GetGenShinCos():
    def __init__(self) -> None:
        """
        类，利用`playwright`获取网站`www.miyoushe.com`的搜索结果,返回获取的图片
        ### author
        Cvandia(www.github.com/Cvandia)
        ### version
        1.0.0
        ### usage
        GetGenShinCos()
        """
        self.url = "https://www.miyoushe.com/ys/home/49?type=2"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"
        }
        self.playwright = None
        self.brower = None
        self.con_text = None
        self.page = None
        self.guid_links = None
        self.new_page = None
        self.pic_iamges = None
        self.video_links = None

    async def start(self) -> None:
        """
        启动浏览器
        """
        self.playwright = await async_playwright().start()
        self.brower = await self.playwright.chromium.launch(headless=True)
        self.con_text = await self.brower.new_context()
        await self.con_text.set_extra_http_headers(headers=self.headers)
        self.page = await self.con_text.new_page()

    async def get_page(self, seconds: int) -> io.BytesIO:
        """
        获取页面

        params
        ----
        seconds: int 滑轮向下滚动的时间

        return
        ----
        io.BytesIO: 返回页面的图片
        """
        try:
            await self.page.goto(self.url)
            await self.page.wait_for_selector('//*[@id="__layout"]/div/div[2]/div/div/div[2]')
            # 滑轮向下滚动seconds秒
            start_time = time.time()
            while (time.time() - start_time < seconds):
                await self.page.mouse.wheel(delta_y=20, delta_x=0)
                time.sleep(0.01)
            await self.page.wait_for_timeout(2000)
            guid_image = await self.page.locator('div.mhy-article-list__body').screenshot(quality=50,type='jpeg')
            self.guid_links = await self.page.query_selector_all('.mhy-img-article-card__header a')
            image = Image.open(io.BytesIO(guid_image))
            draw = ImageDraw.Draw(image)
            for m in range(len(self.guid_links)):
                x = m % 3  # 0,1,2
                y = m // 3  # 0,1,2,3,4,5
                draw.text((x*247, y*247), str(m), fill=(255, 0, 0),
                        font=ImageFont.truetype(font=font_path, size=100))
            byes = io.BytesIO()
            image.save(byes, format="JPEG")
            return byes
        except Exception as exc:
            await self.close()
            raise exc

    async def get_img_or_video(self, location:List[int]) -> Tuple[int, list]:
        """
        获取图片或视频链接

        params
        ----

        return
        ----
        tuple[int,list] 返回一个元组，第一个元素为0表示图片，为1表示视频，第二个元素为图片或视频的链接列表
        """
        url_list = []
        locations = list(map(int, location))
        try:
            for i in locations:
                await self.guid_links[i].click()
                async with self.page.expect_popup() as new_page_info:
                    new_page = await new_page_info.value
                    await new_page.wait_for_load_state('networkidle')
                    pic_images = await new_page.query_selector_all('div.mhy-img-article img')
                    video_links = await new_page.query_selector_all('.mhy-video-player__video video')
                    url_list.extend([await pic.get_attribute('large') for pic in pic_images])
                    await new_page.close()
        except Exception as exp:
            await self.close()
            raise exp
        # 获取图片链接
        if pic_images:
            return 0,url_list
        # 如果图片不存在则获取获取视频链接
        else:
            return 1,url_list

    async def get_all_img(self) -> list:
        """
        获取所有图片链接

        return
        ----
        list 返回所有图片链接
        """
        img_list = []
        try:
            self.guid_links = await self.page.query_selector_all('.mhy-img-article-card__header a')
            for link in self.guid_links:
                await link.click()
                async with self.page.expect_popup() as new_page_info:
                    new_page = await new_page_info.value
                    await new_page.wait_for_load_state('networkidle')
                    pic_images = await new_page.query_selector_all('div.mhy-img-article img')
                    for i in pic_images:
                        img_list.append(await i.get_attribute('large'))
                    await new_page.close()
            return img_list
        except Exception:
            await self.close()

    async def close(self) -> None:
        """
        关闭浏览器
        """
        await self.brower.close()
        await self.playwright.stop()


def check_cd(user_id: int, user_data: dict) -> Tuple[bool, int, dict]:
    """检查用户触发事件的cd

    Args:
        user_id (int): 用户的id
        user_data (dict): 用户数据

    Returns:
        Tuple[bool,int,dict]: 返回一个元组，第一个元素为True表示可以触发，为False表示不可以触发，第二个元素为剩余时间，第三个元素为用户数据
    """
    data = user_data
    if str(user_id) not in data:
        data[str(user_id)] = datetime.now()
    if datetime.now() < data[f'{user_id}']:
        delta = (data[str(user_id)] - datetime.now()).seconds
        return False, delta, data
    else:
        data[str(user_id)] = datetime.now() + timedelta(seconds=cd)
        return True, 0, data
    
def log(front:str,behind:str,*args, **kwargs):
    """
    自定义`nonebot2`的log输出

    Args:
        front (str): 前面的文字
        behind (str): 后面的文字
    
    Returns:
        log输出，格式为`[front] behind`
    """
    blog.opt(colors=True).info(f"<u><y>[{front}]</y></u>{behind}")

##############################################################################################################
# 别看了，这里能有啥？
# 代码依托答辩