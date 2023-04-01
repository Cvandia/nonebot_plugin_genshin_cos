import requests
from nonebot.log import logger
from pathlib import Path
from typing import Tuple
from nonebot import get_driver
from .config import Config
from datetime import datetime,timedelta
try:
    import ujson as json
except ImportError:
    import json
import random
import re

cd = Config.parse_obj(get_driver().config.dict()).cos_cd
    
class WriteError(Exception):
    pass
        
class get_cos(object):
    """获取米游社原神cos最新图片"""
    def __init__(self) -> None:
        self.url = "https://bbs-api.mihoyo.com/post/wapi/getForumPostList?forum_id=49"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/92.0.4515.107 Safari/537.36'
        }
    def parse(self):
        """获取网页数据"""
        img_dict_data = {}         
        res = requests.get(self.url, headers=self.headers).text          
        res = json.loads(res)         
        res = res['data']['list']        
        subject_name = [i['post']['subject'] for i in res]         
        cover_url = [i['post']['cover'] for i in res]
        for name, url in zip(subject_name, cover_url):
            img_dict_data[name] = url
        return img_dict_data
    
    
    def get_img_url(self) ->list:
        """获取cos图片链接列表"""
        data = self.parse()
        img_list = []
        for k,v in data.items():
            img_list.append(v)
        return img_list
    
    def get_img_name(self) ->list:
        """获取cos图片名称

        Returns:
            list: 图片名称列表
        """
        data = self.parse()
        name_list = []
        for k,v in data.items():
            name_list.append(k)
        return name_list
    
    
    def save_img(self,save_path:str):
        """保存cos的图片
        save_path: 保存的路劲
        
        返回：
        int:成功保存的数量
        """
        data = self.parse()
        path = Path(save_path)
        if not str(save_path):
            path = Path("./data/genshin_cos")
        if not path.exists():
            path.mkdir(parents=True)
            logger.warning(f"文件夹不存在，正在创建文件夹:{path}")
        N = 0
        for k,v in data.items():
            N += 1
            k = re.sub(r'[^\w]', '',k)
            try:
                with open(path / f"{k}.jpg", 'wb') as f:
                    img = requests.get(v, headers=self.headers).content  # 发送请求获取图片内容
                    f.write(img)
                    logger.success(f"保存成功 --> {k}")
            except Exception as exc:
                logger.error(exc)
                raise WriteError(f"出错了请查看详细报错:\n{exc}")
        return N
    
    def randow_cos_img(self) ->str:
        """随机cos图链接"""
        return random.choice(self.get_img_url())
    
    def download_urls(self,urls:list,names:list,save_path:str) ->int:
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
        for url,name in zip(urls,names):
            N += 1
            name = re.sub(r'[^\w]', '',name)
            try:
                with open(path / f"{name}.jpg", 'wb') as f:
                    img = requests.get(url, headers=self.headers).content
                    f.write(img)
                    logger.success(f"保存成功 --> {name}")
            except Exception as exc:
                raise WriteError(exc)
        return N
    
def check_cd(user_id:int, user_data:dict) ->Tuple[bool,int,dict]:
    """检查用户触发事件的cd

    Args:
        user_id (int): 用户的id
        user_data (dict): 用户数据

    Returns:
        Tuple[bool,int,dict]: 返回元组（是否超出cd，剩余cd，更新后的用户数据）
    """
    data = user_data
    if str(user_id) not in data:
        data[str(user_id)] = datetime.now() + timedelta(seconds=cd)
    if datetime.now() < data[f'{user_id}']:
        delta = (data[str(user_id)] - datetime.now()).seconds
        return False,delta,data
    else:
        data[str(user_id)] = datetime.now() + timedelta(seconds=cd)
        return True, 0, data

