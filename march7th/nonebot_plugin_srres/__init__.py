from nonebot.log import logger
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot import require, get_driver, on_command

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_datastore")
require("nonebot_plugin_saa")

from nonebot_plugin_apscheduler import scheduler
from nonebot_plugin_saa import Text, MessageFactory

from .data_source import StarRailRes

__plugin_meta__ = PluginMetadata(
    name="StarRailRes",
    description="崩坏：星穹铁道资源",
    usage="""\
更新索引: srupdate *superuser
""",
    extra={
        "version": "1.0",
        "srhelp": """\
更新索引: srupdate [color=gray]*superuser[/color]
""",
    },
)

srres = StarRailRes()

driver = get_driver()


@driver.on_startup
async def _():
    if await srres.update():
        logger.info("游戏资源列表加载完成")
    else:
        logger.error("游戏资源列表加载失败，请检查网络连接")
    scheduler.add_job(srres.update, "cron", day=1, id="srres_update")
    logger.info("游戏资源列表自动更新任务已添加")


sr_update = on_command(
    "srupdate", aliases={"更新星铁资源列表"}, permission=SUPERUSER, block=True
)


@sr_update.handle()
async def _():
    msg_builder = MessageFactory([Text("开始更新『崩坏：星穹铁道』游戏资源列表")])
    await msg_builder.send()
    status = await srres.update()
    if not status:
        msg_builder = MessageFactory(
            [Text("『崩坏：星穹铁道』游戏资源列表更新失败，请查看控制台输出")]
        )
    else:
        msg_builder = MessageFactory([Text("『崩坏：星穹铁道』游戏资源列表更新完成")])
    await msg_builder.finish()
