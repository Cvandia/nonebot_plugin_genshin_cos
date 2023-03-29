from typing import Optional
from pydantic import Extra, BaseModel

class Config(BaseModel,extra=Extra.ignore):
    cos_max:int = 5
    