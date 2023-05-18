from nonebot import get_driver
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from .api import MysApi

__plugin_meta__ = PluginMetadata(
    name="MysApi",
    description="米游社API接口",
    usage="",
    extra={
        "version": "1.0",
    },
)

mys_api = MysApi()
driver = get_driver()


@driver.on_startup
async def _():
    await mys_api.init_device()
    logger.info("Device id & fp refreshed")
