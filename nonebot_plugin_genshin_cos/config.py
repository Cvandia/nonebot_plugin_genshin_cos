from typing import Optional
from pydantic import Extra, BaseModel
from pathlib import Path

class Config(BaseModel,extra=Extra.ignore):
    cos_max:int = 5
    cos_path:Optional[str] = ""
    cos_cd:int = 10
    