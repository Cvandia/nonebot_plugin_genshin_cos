from nonebot import get_driver
from nonebot.log import logger

"""
Config: 配置类
    - 更新: 解决掉pydantic v2的用户自定义配置类的问题
"""
class Config():
    def __init__(self) -> None:
        driver_config = get_driver().config
        try:
            self.cos_max = driver_config.cos_max
        except:
            logger.warning("未找到用户自定义配置 cos_max，使用默认配置")
            self.cos_max = 10

        try:
            self.cos_path = driver_config.cos_path
        except :
            logger.warning("未找到用户自定义配置 cos_path，使用默认配置")
            self.cos_path = ""

        try:
            self.cos_cd = driver_config.cos_cd
        except:
            logger.warning("未找到用户自定义配置 cos_cd，使用默认配置")
            self.cos_cd = 10

        try:
            self.cos_forward_msg = driver_config.cos_forward_msg
        except:
            logger.warning("未找到用户自定义配置 cos_forward_msg，使用默认配置")
            self.cos_forward_msg = False

        try:
            self.cos_delay = driver_config.cos_delay
        except:
            logger.warning("未找到用户自定义配置 cos_delay，使用默认配置")
            self.cos_delay = 0.5

        try:
            self.is_lagrange = driver_config.is_lagrange
        except:
            logger.warning("未找到用户自定义配置 is_lagrange，使用默认配置")
            self.is_lagrange = False

'''
实例化配置类
'''
config = Config()
