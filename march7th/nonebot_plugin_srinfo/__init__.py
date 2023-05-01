from nonebot import on_command, require
from nonebot.adapters import Bot, Event, Message
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_saa")
require("nonebot_plugin_srbind")
require("nonebot_plugin_mys_api")

from nonebot_plugin_saa import Image, MessageFactory, Text

try:
    from march7th.nonebot_plugin_mys_api import get_mihoyo_public_data
    from march7th.nonebot_plugin_srbind import get_user_srbind
    from march7th.nonebot_plugin_srbind.cookie import get_public_cookie, get_user_cookie
except ModuleNotFoundError:
    from nonebot_plugin_mys_api import get_mihoyo_public_data
    from nonebot_plugin_srbind import get_user_srbind
    from nonebot_plugin_srbind.cookie import get_user_cookie, get_public_cookie

from .get_img import get_srinfo_img

__plugin_meta__ = PluginMetadata(
    name="StarRailInfo",
    description="崩坏：星穹铁道账号信息查询",
    usage="srinfo",
    extra={
        "version": "1.0",
    },
)

srinfo = on_command("srinfo", aliases={"星铁信息", "星铁账号信息"}, priority=2, block=True)


@srinfo.handle()
async def _(bot: Bot, event: Event, arg: Message = CommandArg()):
    user_list = await get_user_srbind(bot.self_id, event.get_user_id())
    if not user_list:
        msg = "未绑定SRUID"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srinfo.finish()
    sr_uid = user_list[0].sr_uid
    cookie = await get_user_cookie(bot.self_id, event.get_user_id(), sr_uid)
    if not cookie:
        cookie = await get_public_cookie(bot.self_id)
    if not cookie:
        msg = "当前无可用cookie"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srinfo.finish()
    logger.info(f"正在查询SRUID『{sr_uid}』信息")
    sr_basic_info = await get_mihoyo_public_data(sr_uid, cookie, mode="sr_basic_info")
    sr_index = await get_mihoyo_public_data(sr_uid, cookie, mode="sr_index")
    if (
        not sr_basic_info
        or not sr_index
        or sr_basic_info["retcode"] == 999
        or sr_index["retcode"] == 999
    ):
        msg = "查询失败，请稍后重试"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srinfo.finish()
    logger.info(f"正在绘制SRUID『{sr_uid}』信息图片")
    img = await get_srinfo_img(sr_uid, sr_basic_info, sr_index)
    if img:
        msg_builder = MessageFactory([Image(img)])
    else:
        msg_builder = MessageFactory([Text("图片绘制失败，请稍后重试")])
    await msg_builder.send(at_sender=True)
    await srinfo.finish()
