from nonebot import get_driver, require
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

from .api import MysApi

__plugin_meta__ = PluginMetadata(
    name="MysApi",
    description="米游社API接口",
    usage="",
    extra={
        "version": "1.0",
    },
)

driver = get_driver()
mys_api = MysApi(driver)


@driver.on_startup
async def _():
    await mys_api.init_device()
    logger.debug("Device id & fp refreshed")


@scheduler.scheduled_job("interval", minutes=5, id="refresh_device")
async def refresh_device():
    await mys_api.init_device()
    logger.debug("Device id & fp refreshed")
