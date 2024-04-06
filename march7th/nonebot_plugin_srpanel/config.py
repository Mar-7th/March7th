from typing import Optional

from pydantic import BaseModel
from nonebot import get_plugin_config


class Config(BaseModel):
    sr_panel_url: Optional[str] = "https://api.mihomo.me/sr_info_parsed/"
    github_proxy: Optional[str] = "https://mirror.ghproxy.com"
    sr_score_url: Optional[str] = (
        "https://raw.githubusercontent.com/Mar-7th/StarRailScore/master/score.json"
    )


plugin_config = get_plugin_config(Config)
