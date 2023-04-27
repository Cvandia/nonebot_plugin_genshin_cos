from typing import Optional
from pydantic import Extra, BaseModel
from pathlib import Path

class Config(BaseModel,extra=Extra.ignore):
    cos_max:int = 5
    cos_path:Optional[str] = ""
    cos_cd:int = 30
    cos_time_out:int = 60
    cos_swipe_time:int = 1