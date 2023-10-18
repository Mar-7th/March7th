from nonebot.plugin import PluginMetadata

from .api import MysApi as MysApi

__plugin_meta__ = PluginMetadata(
    name="MysApi",
    description="米游社API接口",
    usage="",
    extra={
        "version": "1.0",
    },
)
