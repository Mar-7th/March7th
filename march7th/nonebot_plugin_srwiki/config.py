from typing import Optional

from nonebot import get_driver
from pydantic import BaseModel, Extra

MAPPING_CN_FILE_NAME = "mapping_cn.json"
CHARACTER_FILE_NAME = "character.json"
LIGHT_CONE_FILE_NAME = "light_cone.json"


class Config(BaseModel, extra=Extra.ignore):
    github_proxy: Optional[str] = "https://github.moeyy.xyz"
    sr_wiki_url: Optional[
        str
    ] = "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master"


plugin_config = Config(**get_driver().config.dict())
