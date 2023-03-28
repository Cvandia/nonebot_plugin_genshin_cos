import requests
from pathlib import Path
try:
    import ujson as json
except ImportError:
    import json
import random
    
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
    
    
    def save_img(self,save_path:Path):
        """保存cos的图片\nsave_path: 保存的路劲"""
        data = self.parse()
        if not save_path:
            save_path = Path("data/genshin_cos")
            #如果目录不存在就创建该目录
            save_path.parent.mkdir(parents=True, exist_ok=True)
        for k,v in data:
            try:
                with open(f"{save_path}/{k}.png", 'wb') as f:
                    img = requests.get(v, headers=self.headers).content  # 发送请求获取图片内容
                    f.write(img)
            except OSError:
                raise WriteError("读写出错了")
    
    def randow_cos_img(self) ->str:
        """随机cos图链接"""
        return random.choice(self.get_img_url())