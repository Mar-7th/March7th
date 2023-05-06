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
    from march7th.nonebot_plugin_srbind.cookie import (
        get_public_cookie,
        get_user_cookie,
        set_cookie_expire,
    )
except ModuleNotFoundError:
    from nonebot_plugin_mys_api import call_mihoyo_api
    from nonebot_plugin_srbind import get_user_srbind
    from nonebot_plugin_srbind.cookie import (
        get_public_cookie,
        get_user_cookie,
        set_cookie_expire,
    )

from .get_img import get_srinfo_img

__plugin_meta__ = PluginMetadata(
    name="StarRailInfo",
    description="崩坏：星穹铁道账号信息查询",
    usage="""\
查看信息:   srinfo
""",
    extra={
        "version": "1.0",
    },
)

srinfo = on_command("srinfo", aliases={"星铁信息", "星铁账号信息"}, priority=2, block=True)


@srinfo.handle()
async def _(bot: Bot, event: Event):
    user_list = await get_user_srbind(bot.self_id, event.get_user_id())
    if not user_list:
        msg = "未绑定SRUID，请使用`sruid [uid]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srinfo.finish()
    sr_uid = user_list[0].sr_uid
    cookie = await get_user_cookie(bot.self_id, event.get_user_id(), sr_uid)
    public_cookie_flag = False
    if not cookie:
        cookie = await get_public_cookie(bot.self_id)
        public_cookie_flag = True
    if not cookie:
        msg = "当前无可用cookie"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srinfo.finish()
    logger.info(f"正在查询SRUID『{sr_uid}』信息")
    sr_basic_info = await call_mihoyo_api(
        api="sr_basic_info", cookie=cookie, role_uid=sr_uid
    )
    sr_index = await call_mihoyo_api(api="sr_index", cookie=cookie, role_uid=sr_uid)
    try:
        avatar_id = sr_index["avatar_list"][0]["id"] if sr_index else None
    except (KeyError, IndexError):
        avatar_id = None
    # cookie expire if avatar_id is None
    if not avatar_id:
        if public_cookie_flag:
            logger.warning(f"公共cookie已失效")
            msg = "公共cookie已失效，请使用`srqr`扫码绑定账号"
            msg_builder = MessageFactory([Text(str(msg))])
        else:
            await set_cookie_expire(bot.self_id, event.get_user_id(), sr_uid)
            logger.info(f"已删除SRUID『{sr_uid}』的过期cookie")
            msg = "你的cookie疑似失效了，请重新使用`srqr`扫码绑定"
            msg_builder = MessageFactory([Text(str(msg))])
    else:
        sr_avatar_info = await call_mihoyo_api(
            api="sr_avatar_info", cookie=cookie, role_uid=sr_uid, avatar_id=avatar_id
        )
        if not sr_basic_info or not sr_index or not sr_avatar_info:
            msg = "查询失败，请稍后重试"
            msg_builder = MessageFactory([Text(str(msg))])
            await msg_builder.send(at_sender=True)
            await srinfo.finish()
        logger.info(f"正在绘制SRUID『{sr_uid}』信息图片")
        img = await get_srinfo_img(sr_uid, sr_basic_info, sr_index, sr_avatar_info)
        if img:
            msg_builder = MessageFactory([Image(img)])
        else:
            msg_builder = MessageFactory([Text("图片绘制失败，请稍后重试")])
    await msg_builder.send(at_sender=True)
    await srinfo.finish()
