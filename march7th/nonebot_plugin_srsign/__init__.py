from nonebot import require
from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_saa")
require("nonebot_plugin_mys_api")
require("nonebot_plugin_srbind")

from nonebot_plugin_saa import MessageFactory, Text

try:
    from march7th.nonebot_plugin_mys_api import mys_api
    from march7th.nonebot_plugin_srbind import get_user_srbind
    from march7th.nonebot_plugin_srbind.cookie import get_user_cookie
except ModuleNotFoundError:
    from nonebot_plugin_mys_api import mys_api
    from nonebot_plugin_srbind import get_user_srbind
    from nonebot_plugin_srbind.cookie import get_user_cookie

__plugin_meta__ = PluginMetadata(
    name="StarRailSign",
    description="崩坏：星穹铁道米游社签到",
    usage="srsign",
    extra={
        "version": "1.0",
        "srhelp": """\
每日签到: srsign
""",
    },
)

error_code_msg = {
    10001: "绑定cookie失效，请重新绑定",
    -10001: "请求出错，请尝试重新使用`srqr`绑定",
    -5003: "今日已签到",
}

srsign = on_command(
    "srsign", aliases={"星铁签到", "星铁每日签到", "米游社签到"}, priority=2, block=True
)


@srsign.handle()
async def _(bot: Bot, event: Event):
    global msg, error_message
    user_list = await get_user_srbind(bot.self_id, event.get_user_id())
    if not user_list:
        msg = "未绑定SRUID，请使用`sruid [uid]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srsign.finish()
    sr_uid = user_list[0].sr_uid
    cookie = await get_user_cookie(bot.self_id, event.get_user_id(), sr_uid)
    if not cookie:
        msg = "未绑定cookie，请使用`srck [cookie]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srsign.finish()
    logger.info(f"开始为SRUID『{sr_uid}』签到")
    await srsign.send(f"开始为SRUID『{sr_uid}』签到")
    sr_sign = await mys_api.call_mihoyo_api("sr_sign", cookie=cookie, role_uid=sr_uid)
    if isinstance(sr_sign, int):
        if sr_sign in error_code_msg:
            msg = error_code_msg[sr_sign]
        else:
            msg = f"签到失败，请稍后重试（错误代码 {sr_sign}）"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srsign.finish()
    if not sr_sign:
        msg = "疑似cookie失效，请重新使用`srck [cookie]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srsign.finish()
    is_risk = sr_sign.get("is_risk")
    if is_risk is True:
        msg = "签到遇验证码，请手动签到"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srsign.finish()
    msg = "签到成功"
    msg_builder = MessageFactory([Text(str(msg))])
    await msg_builder.send(at_sender=True)
    await srsign.finish()
