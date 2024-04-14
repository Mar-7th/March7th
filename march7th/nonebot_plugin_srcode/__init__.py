from nonebot.adapters import Event
from nonebot import require, on_command
from nonebot.plugin import PluginMetadata

from .data_source import get_code_msg

require("nonebot_plugin_saa")

from nonebot_plugin_saa import Text, MessageFactory

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
async def _(event: Event):
    try:
        codes = await get_code_msg()
    except Exception:
        codes = "获取前瞻兑换码失败"
    msg_builder = MessageFactory([Text(str(codes))])
    await msg_builder.finish(at_sender=not event.is_tome())
