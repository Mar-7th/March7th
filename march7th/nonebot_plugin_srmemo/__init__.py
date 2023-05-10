from nonebot import on_command, require
from nonebot.adapters import Bot, Event
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_saa")
require("nonebot_plugin_mys_api")
require("nonebot_plugin_srbind")
require("nonebot_plugin_srres")

from nonebot_plugin_saa import Image, MessageFactory, Text

try:
    from march7th.nonebot_plugin_mys_api import call_mihoyo_api
    from march7th.nonebot_plugin_srbind import get_user_srbind
    from march7th.nonebot_plugin_srbind.cookie import get_user_cookie
except ModuleNotFoundError:
    from nonebot_plugin_mys_api import call_mihoyo_api
    from nonebot_plugin_srbind import get_user_srbind
    from nonebot_plugin_srbind.cookie import (
        get_user_cookie,
    )

from .get_img import get_srmemo_img, get_srmonth_img

__plugin_meta__ = PluginMetadata(
    name="StarRailMemo",
    description="崩坏：星穹铁道开拓信息查询",
    usage="""\
实时便笺: srmemo
开拓月历: srmonth
""",
    extra={
        "version": "1.0",
        "srhelp": """\
实时便笺: srmemo
开拓月历: srmonth
""",
    },
)

srmemo = on_command(
    "srmemo",
    aliases={"srnote", "星铁体力", "星铁每日", "星铁开拓力", "星铁便笺", "星铁实时便笺"},
    priority=2,
    block=True,
)
srmonth = on_command(
    "srmonth", aliases={"星铁每月", "星铁月历", "星铁开拓月历"}, priority=2, block=True
)


@srmemo.handle()
async def _(bot: Bot, event: Event):
    user_list = await get_user_srbind(bot.self_id, event.get_user_id())
    if not user_list:
        msg = "未绑定SRUID，请使用`sruid [uid]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srmemo.finish()
    sr_uid = user_list[0].sr_uid
    cookie = await get_user_cookie(bot.self_id, event.get_user_id(), sr_uid)
    if not cookie:
        msg = "未绑定cookie，请使用`srck [cookie]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srmemo.finish()
    logger.info(f"正在查询SRUID『{sr_uid}』便笺")
    sr_basic_info = await call_mihoyo_api(
        api="sr_basic_info", cookie=cookie, role_uid=sr_uid
    )
    sr_note = await call_mihoyo_api(api="sr_note", cookie=cookie, role_uid=sr_uid)
    if not sr_basic_info or not sr_note:
        msg = "查询失败，请稍后重试"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srmemo.finish()
    logger.info(f"正在绘制SRUID『{sr_uid}』便笺图片")
    img = await get_srmemo_img(sr_uid, sr_basic_info, sr_note)
    if img:
        msg_builder = MessageFactory([Image(img)])
    else:
        msg_builder = MessageFactory([Text("图片绘制失败，请稍后重试")])
    await msg_builder.send(at_sender=True)
    await srmemo.finish()


@srmonth.handle()
async def _(bot: Bot, event: Event):
    user_list = await get_user_srbind(bot.self_id, event.get_user_id())
    if not user_list:
        msg = "未绑定SRUID，请使用`sruid [uid]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srmonth.finish()
    sr_uid = user_list[0].sr_uid
    cookie = await get_user_cookie(bot.self_id, event.get_user_id(), sr_uid)
    if not cookie:
        msg = "未绑定cookie，请使用`srck [cookie]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srmonth.finish()
    logger.info(f"正在查询SRUID『{sr_uid}』月历")
    sr_basic_info = await call_mihoyo_api(
        api="sr_basic_info", cookie=cookie, role_uid=sr_uid
    )
    sr_month = await call_mihoyo_api(
        api="sr_month_info", cookie=cookie, role_uid=sr_uid
    )
    if not sr_basic_info or not sr_month:
        msg = "查询失败，请稍后重试"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srmonth.finish()
    logger.info(f"正在绘制SRUID『{sr_uid}』月历图片")
    img = await get_srmonth_img(sr_uid, sr_basic_info, sr_month)
    if img:
        msg_builder = MessageFactory([Image(img)])
    else:
        msg_builder = MessageFactory([Text("图片绘制失败，请稍后重试")])
    await msg_builder.send(at_sender=True)
    await srmonth.finish()
