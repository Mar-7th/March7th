from nonebot.log import logger
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot import require, get_driver, on_command

require("nonebot_plugin_saa")
require("nonebot_plugin_localstore")
require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler
from nonebot_plugin_saa import Text, MessageFactory

from .data_source import StarRailRes

__plugin_meta__ = PluginMetadata(
    name="StarRailRes",
    description="崩坏：星穹铁道资源",
    usage="""\
更新索引: srupdate *superuser
预下载攻略: srgupdate *superuser
强制更新攻略: srfupdate *superuser
""",
    extra={
        "version": "1.0",
        "srhelp": """\
更新索引: srupdate [color=gray]*superuser[/color]
预下载攻略: srgupdate [color=gray]*superuser[/color]
强制更新攻略: srfupdate [color=gray]*superuser[/color]
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

sr_guide_update = on_command(
    "srgupdate", aliases={"更新星铁攻略"}, permission=SUPERUSER, block=True
)

sr_guide_force_update = on_command(
    "srfupdate", aliases={"强制更新星铁攻略"}, permission=SUPERUSER, block=True
)


@sr_update.handle()
async def _():
    msg_builder = MessageFactory([Text("开始更新游戏资源列表")])
    await msg_builder.send()
    status = await srres.update()
    if not status:
        msg_builder = MessageFactory([Text("游戏资源列表更新失败，请查看控制台输出")])
    else:
        msg_builder = MessageFactory([Text("游戏资源列表更新完成")])
    await msg_builder.finish()


@sr_guide_update.handle()
async def _():
    msg_builder = MessageFactory([Text("开始预下载攻略文件，可能需要较长时间")])
    await msg_builder.send()
    status = await srres.download_guide()
    if not status:
        msg_builder = MessageFactory([Text("攻略文件预下载失败，请查看控制台输出")])
    else:
        msg_builder = MessageFactory([Text("攻略文件预下载完成")])
    await msg_builder.finish()


@sr_guide_force_update.handle()
async def _():
    msg_builder = MessageFactory([Text("开始强制更新攻略文件，可能需要较长时间")])
    await msg_builder.send()
    status = await srres.download_guide(True)
    if not status:
        msg_builder = MessageFactory([Text("攻略文件强制更新失败，请查看控制台输出")])
    else:
        msg_builder = MessageFactory([Text("攻略文件强制更新完成")])
    await msg_builder.finish()
