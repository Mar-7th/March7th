from typing import List

from nonebot.log import logger
from nonebot import require, on_command
from nonebot.adapters import Bot, Event
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_saa")
require("nonebot_plugin_mys_api")
require("nonebot_plugin_srbind")

from nonebot_plugin_saa import Text, MessageFactory

try:
    from march7th.nonebot_plugin_mys_api import MysApi
    from march7th.nonebot_plugin_srbind import get_user_srbind
    from march7th.nonebot_plugin_srbind.cookie import (
        set_user_fp,
        get_user_cookie_with_fp,
    )
except ModuleNotFoundError:
    from nonebot_plugin_mys_api import MysApi
    from nonebot_plugin_srbind import get_user_srbind
    from nonebot_plugin_srbind.cookie import set_user_fp, get_user_cookie_with_fp

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
    -100: "请重新使用`srqr`绑定账号",
}

srsign = on_command(
    "srsign", aliases={"星铁签到", "星铁每日签到"}, priority=2, block=True
)


@srsign.handle()
async def _(bot: Bot, event: Event):
    user_id = event.get_user_id()
    user_list = await get_user_srbind(bot.self_id, user_id)
    if not user_list:
        err = "未绑定SRUID，请使用`srck [cookie]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(err)])
        await msg_builder.send(at_sender=not event.is_tome())
        await srsign.finish()
    msg: List[str] = []
    for user in user_list:
        sr_uid = user.sr_uid
        cookie, device_id, device_fp = await get_user_cookie_with_fp(
            bot.self_id, event.get_user_id(), sr_uid
        )
        if not cookie:
            msg.append(
                f"UID{sr_uid}: 未绑定cookie，请使用`srck [cookie]`绑定或`srqr`扫码绑定"
            )
            continue
        logger.info(f"开始为SRUID『{sr_uid}』签到")
        mys_api = MysApi(cookie, device_id, device_fp)
        if not device_id or not device_fp:
            device_id, device_fp = await mys_api.init_device()
        sr_sign = await mys_api.call_mihoyo_api("sr_sign", role_uid=sr_uid)
        if not sr_sign:
            msg.append(
                f"UID{sr_uid}: 疑似cookie失效，请重新使用`srck [cookie]`绑定或`srqr`扫码绑定"
            )
            msg_builder = MessageFactory([Text(str(msg))])
            await msg_builder.send(at_sender=not event.is_tome())
            await srsign.finish()
        if isinstance(sr_sign, int):
            if sr_sign in error_code_msg:
                msg.append(f"UID{sr_uid}: {error_code_msg[sr_sign]}")
            else:
                msg.append(f"UID{sr_uid}: 签到失败（错误代码 {sr_sign}）")
            continue
        is_risk = sr_sign.get("is_risk")
        if is_risk is True:
            msg.append(f"UID{sr_uid}: 签到遇验证码，请手动签到")
        else:
            msg.append(f"UID{sr_uid}: 签到成功")
            if new_fp := sr_sign.get("new_fp"):
                await set_user_fp(
                    bot.self_id, event.get_user_id(), sr_uid, device_id, new_fp
                )
    msg_builder = MessageFactory([Text("\n" + "\n".join(msg))])
    await msg_builder.finish(at_sender=not event.is_tome())
