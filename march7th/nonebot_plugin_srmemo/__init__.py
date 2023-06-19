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
    from march7th.nonebot_plugin_mys_api import mys_api
    from march7th.nonebot_plugin_srbind import get_user_srbind
    from march7th.nonebot_plugin_srbind.cookie import get_user_cookie, get_user_stoken
except ModuleNotFoundError:
    from nonebot_plugin_mys_api import mys_api
    from nonebot_plugin_srbind import get_user_srbind
    from nonebot_plugin_srbind.cookie import get_user_cookie, get_user_stoken

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

error_code_msg = {
    1034: "查询遇验证码，请手动在米游社验证后查询",
    10001: "绑定cookie失效，请重新绑定",
    -10001: "请求出错，请尝试重新使用`srqr`绑定",
}

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
    stoken = await get_user_stoken(bot.self_id, event.get_user_id(), sr_uid)
    if not cookie or not stoken:
        msg = "未绑定cookie，请使用`srck [cookie]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srmemo.finish()
    logger.info(f"正在查询SRUID『{sr_uid}』便笺")
    sr_basic_info = await mys_api.call_mihoyo_api(
        api="sr_basic_info", cookie=cookie, role_uid=sr_uid
    )
    sr_note = await mys_api.call_mihoyo_api(
        api="sr_widget", cookie=stoken, role_uid=sr_uid
    )
    if isinstance(sr_basic_info, int):
        if sr_basic_info in error_code_msg:
            msg = error_code_msg[sr_basic_info]
        else:
            msg = f"查询失败，请稍后重试（错误代码 {sr_basic_info}）"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srmemo.finish()
    if isinstance(sr_note, int):
        if sr_note in error_code_msg:
            msg = error_code_msg[sr_note]
        else:
            msg = f"查询失败，请稍后重试（错误代码 {sr_note}）"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srmemo.finish()
    if not sr_basic_info or not sr_note:
        msg = "疑似cookie失效，请重新使用`srck [cookie]`绑定或`srqr`扫码绑定"
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
    sr_basic_info = await mys_api.call_mihoyo_api(
        api="sr_basic_info", cookie=cookie, role_uid=sr_uid
    )
    sr_month = await mys_api.call_mihoyo_api(
        api="sr_month_info", cookie=cookie, role_uid=sr_uid
    )
    if isinstance(sr_basic_info, int):
        if sr_basic_info in error_code_msg:
            msg = error_code_msg[sr_basic_info]
        else:
            msg = f"查询失败，请稍后重试（错误代码 {sr_basic_info}）"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srmonth.finish()
    if isinstance(sr_month, int):
        if sr_month in error_code_msg:
            msg = error_code_msg[sr_month]
        else:
            msg = f"查询失败，请稍后重试（错误代码 {sr_month}）"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srmonth.finish()
    if not sr_basic_info or not sr_month:
        msg = "疑似cookie失效，请重新使用`srck [cookie]`绑定或`srqr`扫码绑定"
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
