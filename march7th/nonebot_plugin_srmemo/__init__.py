from nonebot.log import logger
from nonebot import require, on_command
from nonebot.adapters import Bot, Event
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_saa")
require("nonebot_plugin_mys_api")
require("nonebot_plugin_srbind")
require("nonebot_plugin_srres")

from nonebot_plugin_saa import Text, Image, MessageFactory

try:
    from march7th.nonebot_plugin_mys_api import MysApi
    from march7th.nonebot_plugin_srbind import get_user_srbind
    from march7th.nonebot_plugin_srbind.cookie import (
        set_user_fp,
        get_user_stoken,
        get_user_cookie_with_fp,
    )
except ModuleNotFoundError:
    from nonebot_plugin_mys_api import MysApi
    from nonebot_plugin_srbind import get_user_srbind
    from nonebot_plugin_srbind.cookie import (
        get_user_cookie_with_fp,
        get_user_stoken,
        set_user_fp,
    )

from .data_source import get_srmemo_img, get_srmonth_img

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
    1034: "查询遇验证码",
    10001: "绑定cookie失效，请重新绑定",
    -10001: "请求出错，请稍后重试",
}

srmemo = on_command(
    "srmemo",
    aliases={
        "srnote",
        "星铁体力",
        "星铁每日",
        "星铁开拓力",
        "星铁便笺",
        "星铁实时便笺",
    },
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
        await msg_builder.finish(at_sender=not event.is_tome())
    sr_uid = user_list[0].sr_uid
    cookie, device_id, device_fp = await get_user_cookie_with_fp(
        bot.self_id, event.get_user_id(), sr_uid
    )
    stoken = await get_user_stoken(bot.self_id, event.get_user_id(), sr_uid)
    if not cookie or not stoken:
        msg = "未绑定cookie，请使用`srck [cookie]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.finish(at_sender=not event.is_tome())
    logger.info(f"正在查询SRUID『{sr_uid}』便笺")
    mys_api = MysApi(cookie, device_id, device_fp)
    if not device_id or not device_fp:
        device_id, device_fp = await mys_api.init_device()
    sr_basic_info = await mys_api.call_mihoyo_api(api="sr_basic_info", role_uid=sr_uid)
    sr_note = await mys_api.call_mihoyo_api(api="sr_note", role_uid=sr_uid)
    if isinstance(sr_basic_info, int):
        if sr_basic_info in error_code_msg:
            msg = error_code_msg[sr_basic_info]
        else:
            msg = f"查询失败，请稍后重试（错误代码 {sr_basic_info}）"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.finish(at_sender=not event.is_tome())
    if isinstance(sr_note, int):
        if sr_note in error_code_msg:
            msg = error_code_msg[sr_note]
        else:
            msg = f"查询失败，请稍后重试（错误代码 {sr_note}）"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.finish(at_sender=not event.is_tome())
    if not sr_basic_info or not sr_note:
        msg = "疑似cookie失效，请重新使用`srck [cookie]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.finish(at_sender=not event.is_tome())
    if new_fp := sr_note.get("new_fp"):
        await set_user_fp(bot.self_id, event.get_user_id(), sr_uid, device_id, new_fp)
    logger.info(f"正在绘制SRUID『{sr_uid}』便笺图片")
    img = await get_srmemo_img(sr_uid, sr_basic_info, sr_note)
    if img:
        msg_builder = MessageFactory([Image(img)])
    else:
        msg_builder = MessageFactory([Text("图片绘制失败，请稍后重试")])
    await msg_builder.finish()


@srmonth.handle()
async def _(bot: Bot, event: Event):
    user_list = await get_user_srbind(bot.self_id, event.get_user_id())
    if not user_list:
        msg = "未绑定SRUID，请使用`sruid [uid]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.finish(at_sender=not event.is_tome())
    sr_uid = user_list[0].sr_uid
    cookie, device_id, device_fp = await get_user_cookie_with_fp(
        bot.self_id, event.get_user_id(), sr_uid
    )
    if not cookie:
        msg = "未绑定cookie，请使用`srck [cookie]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.finish(at_sender=not event.is_tome())
    logger.info(f"正在查询SRUID『{sr_uid}』月历")
    mys_api = MysApi(cookie, device_id, device_fp)
    if not device_id or not device_fp:
        device_id, device_fp = await mys_api.init_device()
    sr_basic_info = await mys_api.call_mihoyo_api(api="sr_basic_info", role_uid=sr_uid)
    sr_month = await mys_api.call_mihoyo_api(api="sr_month_info", role_uid=sr_uid)
    if isinstance(sr_basic_info, int):
        if sr_basic_info in error_code_msg:
            msg = error_code_msg[sr_basic_info]
        else:
            msg = f"查询失败，请稍后重试（错误代码 {sr_basic_info}）"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.finish(at_sender=not event.is_tome())
    if isinstance(sr_month, int):
        if sr_month in error_code_msg:
            msg = error_code_msg[sr_month]
        else:
            msg = f"查询失败，请稍后重试（错误代码 {sr_month}）"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.finish(at_sender=not event.is_tome())
    if not sr_basic_info or not sr_month:
        msg = "疑似cookie失效，请重新使用`srck [cookie]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.finish(at_sender=not event.is_tome())
    if new_fp := sr_month.get("new_fp"):
        await set_user_fp(bot.self_id, event.get_user_id(), sr_uid, device_id, new_fp)
    logger.info(f"正在绘制SRUID『{sr_uid}』月历图片")
    img = await get_srmonth_img(sr_uid, sr_basic_info, sr_month)
    if img:
        msg_builder = MessageFactory([Image(img)])
    else:
        msg_builder = MessageFactory([Text("图片绘制失败，请稍后重试")])
    await msg_builder.finish()
