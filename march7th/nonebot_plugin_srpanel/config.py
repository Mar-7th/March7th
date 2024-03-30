from typing import Optional

from nonebot import get_driver
from pydantic import Extra, BaseModel


class Config(BaseModel, extra=Extra.ignore):
    sr_panel_url: Optional[str] = "https://api.mihomo.me/sr_info_parsed/"
    github_proxy: Optional[str] = "https://mirror.ghproxy.com"
    sr_score_url: Optional[
        str
    ] = "https://raw.githubusercontent.com/Mar-7th/StarRailScore/master/score.json"


plugin_config = Config(**get_driver().config.dict())
