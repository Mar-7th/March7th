from typing import Optional

from nonebot import get_driver
from pydantic import Extra, BaseModel


class Config(BaseModel, extra=Extra.ignore):
    github_proxy: Optional[str] = "https://mirror.ghproxy.com"
    sr_wiki_url: Optional[
        str
    ] = "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master"
    # file, base64
    # 当QQ客户端与bot端不在同一台计算机时，可用 base64 协议
    sr_wiki_send_protocol: Optional[str] = "file"


plugin_config = Config(**get_driver().config.dict())

# 若非可选值则重置回默认
if plugin_config.sr_wiki_send_protocol not in ["file", "base64"]:
    plugin_config.sr_wiki_send_protocol = "file"
