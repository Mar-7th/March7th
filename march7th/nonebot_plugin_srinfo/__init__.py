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
    from march7th.nonebot_plugin_srbind.cookie import (  # set_cookie_expire,
        set_user_fp,
        set_public_fp,
        get_user_cookie_with_fp,
        get_public_cookie_with_fp,
    )
except ModuleNotFoundError:
    from nonebot_plugin_mys_api import MysApi
    from nonebot_plugin_srbind import get_user_srbind
    from nonebot_plugin_srbind.cookie import (
        get_public_cookie_with_fp,
        get_user_cookie_with_fp,
        set_public_fp,
        set_user_fp,
    )

from .data_source import get_srinfo_img

__plugin_meta__ = PluginMetadata(
    name="StarRailInfo",
    description="崩坏：星穹铁道账号信息查询",
    usage="""\
查看信息: srinfo
""",
    extra={
        "version": "1.0",
        "srhelp": """\
查看信息: srinfo
""",
    },
)


error_code_msg = {
    1034: "查询遇验证码",
    10001: "绑定cookie失效，请重新绑定",
    -10001: "请求出错，请稍后重试",
}

srinfo = on_command(
    "srinfo", aliases={"星铁信息", "星铁账号信息"}, priority=2, block=True
)


@srinfo.handle()
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
    mys_api = MysApi()
    public_cookie_flag = False
    if not device_id or not device_fp:
        device_id, device_fp = await mys_api.init_device()
    if not cookie:
        cookie, device_id, device_fp = await get_public_cookie_with_fp(bot.self_id)
        public_cookie_flag = True
    if not cookie:
        msg = "当前无可用cookie"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.finish(at_sender=not event.is_tome())
    if not device_id or not device_fp:
        device_id, device_fp = await mys_api.init_device()
    logger.info(f"正在查询SRUID『{sr_uid}』信息")
    mys_api = MysApi(cookie, device_id, device_fp)
    sr_basic_info = await mys_api.call_mihoyo_api(api="sr_basic_info", role_uid=sr_uid)
    if isinstance(sr_basic_info, int):
        if sr_basic_info in error_code_msg:
            msg = error_code_msg[sr_basic_info]
        else:
            msg = f"查询失败，错误代码 {sr_basic_info}"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.finish(at_sender=not event.is_tome())
    sr_index = await mys_api.call_mihoyo_api(api="sr_index", role_uid=sr_uid)
    if isinstance(sr_index, int):
        if sr_index in error_code_msg:
            msg = error_code_msg[sr_index]
        else:
            msg = f"查询失败，请稍后重试（错误代码 {sr_index}）"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.finish(at_sender=not event.is_tome())
    try:
        avatar_id = sr_index["avatar_list"][0]["id"] if sr_index else None
    except (KeyError, IndexError):
        avatar_id = None
    # cookie expire if avatar_id is None
    if not avatar_id:
        if public_cookie_flag:
            logger.warning("公共cookie已失效")
            msg = "公共cookie已失效，请使用`srqr`扫码绑定账号"
            msg_builder = MessageFactory([Text(str(msg))])
        else:
            # await set_cookie_expire(bot.self_id, event.get_user_id(), sr_uid)
            # logger.info(f"已删除SRUID『{sr_uid}』的过期cookie")
            msg = "疑似cookie失效，请重新使用`srck [cookie]`绑定或`srqr`扫码绑定"
            msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.finish(at_sender=not event.is_tome())
    sr_avatar_info = await mys_api.call_mihoyo_api(
        api="sr_avatar_info", role_uid=sr_uid, avatar_id=avatar_id
    )
    if isinstance(sr_avatar_info, int):
        sr_avatar_info = None
    if not sr_basic_info or not sr_index:
        msg = "查询失败，请稍后重试"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.finish(at_sender=not event.is_tome())
    if sr_avatar_info and (new_fp := sr_avatar_info.get("new_fp")):
        if not public_cookie_flag:
            await set_user_fp(
                bot.self_id, event.get_user_id(), sr_uid, device_id, new_fp
            )
        else:
            await set_public_fp(bot.self_id, cookie, device_id, new_fp)
    logger.info(f"正在绘制SRUID『{sr_uid}』信息图片")
    img = await get_srinfo_img(sr_uid, sr_basic_info, sr_index, sr_avatar_info)
    if img:
        msg_builder = MessageFactory([Image(img)])
    else:
        msg_builder = MessageFactory([Text("图片绘制失败，请稍后重试")])
    await msg_builder.finish()
