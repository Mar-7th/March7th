from typing import Optional

from pydantic import BaseModel
from nonebot import get_plugin_config


class Config(BaseModel):
    github_proxy: Optional[str] = "https://mirror.ghproxy.com"
    sr_wiki_url: Optional[str] = (
        "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master"
    )


plugin_config = get_plugin_config(Config)
