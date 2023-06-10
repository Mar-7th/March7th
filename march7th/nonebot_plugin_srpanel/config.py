from typing import Optional

from nonebot import get_driver
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    sr_panel_url: Optional[str] = "https://api.mihomo.me/sr_info_parsed/"


plugin_config = Config(**get_driver().config.dict())
