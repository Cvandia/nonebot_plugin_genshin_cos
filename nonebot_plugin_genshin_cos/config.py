from pydantic import Extra, BaseModel


class Config(BaseModel, extra=Extra.ignore):
    cos_max: int = 10
    cos_path: str = "data/genshin_cos"
    cos_cd: int = 30
    cos_forward_msg: bool = True
    cos_delay: float = 0.5
