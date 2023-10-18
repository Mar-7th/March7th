from typing import Optional

from nonebot import get_driver
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    magic_api: Optional[str] = None


plugin_config = Config(**get_driver().config.dict())
