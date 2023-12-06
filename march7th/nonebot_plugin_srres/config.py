from typing import Optional

from nonebot import get_driver
from pydantic import Extra, BaseModel


class Config(BaseModel, extra=Extra.ignore):
    github_proxy: Optional[str] = "https://ghproxy.com"
    sr_wiki_url: Optional[
        str
    ] = "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master"


plugin_config = Config(**get_driver().config.dict())
