from typing import Optional

from pydantic import BaseModel
from nonebot import get_plugin_config


class Config(BaseModel):
    magic_api: Optional[str] = None


plugin_config = get_plugin_config(Config)
