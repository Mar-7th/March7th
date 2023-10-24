from nonebot import on_command, require
from nonebot.plugin import PluginMetadata, on_command

from .data_source import get_code_msg

require("nonebot_plugin_saa")

from nonebot_plugin_saa import MessageFactory, Text

__plugin_meta__ = PluginMetadata(
    name="StarRailCode",
    description="崩坏：星穹铁道前瞻直播兑换码",
    usage="""\
查询兑换码: srcode
""",
    extra={
        "version": "1.0",
        "srhelp": """\
查询兑换码: srcode
""",
    },
)

srcode = on_command("srcode", aliases={"星铁兑换码"})


@srcode.handle()
async def _():
    try:
        codes = await get_code_msg()
    except:
        codes = "获取前瞻兑换码失败"
    msg_builder = MessageFactory([Text(str(codes))])
    await msg_builder.finish(at_sender=True)
