from typing import Optional

from nonebot import get_driver
from pydantic import BaseModel, Extra

CHARACTER_FILE_NAME = "character_cn.json"
LIGHT_CONE_FILE_NAME = "light_cone_cn.json"


class Config(BaseModel, extra=Extra.ignore):
    github_proxy: Optional[str] = "https://github.moeyy.xyz"
    sr_wiki_url: Optional[
        str
    ] = "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master"


plugin_config = Config(**get_driver().config.dict())
