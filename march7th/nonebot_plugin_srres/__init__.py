from nonebot import get_driver, on_command, require
from nonebot.log import logger
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_datastore")
require("nonebot_plugin_saa")

from nonebot_plugin_saa import MessageFactory, Text

from .models import StarRailRes

__plugin_meta__ = PluginMetadata(
    name="StarRailRes",
    description="崩坏：星穹铁道资源",
    usage="""\
更新资源: srupdate *superuser
""",
    extra={
        "version": "1.0",
        "srhelp": """\
更新资源: srupdate [color=gray]*superuser[/color]
""",
    },
)

srres = StarRailRes()

driver = get_driver()


@driver.on_startup
async def _():
    if await srres.update():
        logger.info("『崩坏：星穹铁道』游戏资源加载完成")
    else:
        logger.error("『崩坏：星穹铁道』游戏资源加载失败，请检查网络连接")


sr_update = on_command(
    "srupdate", aliases={"更新星铁资源列表"}, permission=SUPERUSER, block=True
)


@sr_update.handle()
async def _():
    msg_builder = MessageFactory([Text("开始更新『崩坏：星穹铁道』游戏资源")])
    await msg_builder.send()
    await srres.update(update_index=True)
    msg_builder = MessageFactory([Text("『崩坏：星穹铁道』游戏资源更新完成")])
    await msg_builder.send()
    await sr_update.finish()
