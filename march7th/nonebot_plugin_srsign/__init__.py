import anticaptchaofficial.geetestproxyless
from nonebot import get_driver, require
from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_apscheduler")

require("nonebot_plugin_saa")
require("nonebot_plugin_mys_api")
require("nonebot_plugin_srbind")

from nonebot_plugin_saa import MessageFactory, Text

try:
    from march7th.nonebot_plugin_mys_api import mys_api
    from march7th.nonebot_plugin_srbind import get_user_srbind
    from march7th.nonebot_plugin_srbind.cookie import get_user_cookie, get_user_stoken
except ModuleNotFoundError:
    from nonebot_plugin_mys_api import mys_api
    from nonebot_plugin_srbind import get_user_srbind
    from nonebot_plugin_srbind.cookie import get_user_cookie, get_user_stoken

__plugin_meta__ = PluginMetadata(
    name="StarRailSign",
    description="崩坏：星穹铁道米游社签到",
    usage="srsign",
    extra={
        "version": "1.0",
        "srhelp": """\
每日签到: srsign
        """
    }
)

driver = get_driver()
error_code_msg = {
    10001: "绑定cookie失效，请重新绑定",
    -10001: "请求出错，请尝试重新使用`srqr`绑定",
    -5003: "今日已签到"
}
srsign = on_command(
    "srsign",
    aliases={
        "星铁签到",
        "星铁每日签到",
        "米游社签到"
    },
    priority=2,
    block=True
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
    stoken = await get_user_stoken(bot.self_id, event.get_user_id(), sr_uid)
    if not cookie or not stoken:
        msg = "未绑定cookie，请使用`srck [cookie]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srsign.finish()
    logger.info(f"开始为SRUID『{sr_uid}』签到")
    await srsign.send(f"开始为SRUID『{sr_uid}』签到")
    sr_sign_info = await mys_api.call_mihoyo_sign(
        cookie=cookie,
        role_uid=sr_uid
    )

    if isinstance(sr_sign_info, dict):
        retcode = sr_sign_info["retcode"]
        if retcode == 0:
            is_risk = sr_sign_info["data"]["is_risk"]
            if is_risk:
                sr_sign_info, error_message = await geetest_handle(sign_data=sr_sign_info, cookie=cookie, role_uid=sr_uid)
                if isinstance(error_message, dict):
                    retcode = error_message["retcode"]
            else:
                msg = f"SRUID{sr_uid}签到成功成功"
        if retcode in error_code_msg:
            msg = error_code_msg[retcode]
        elif sr_sign_info != 0:
            msg = f"SRUID{sr_uid}签到失败，{error_message}"
        else:
            msg = f"签到失败，请联系管理员\n错误代码{retcode}"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srsign.finish()
    if not sr_sign_info:
        msg = "疑似cookie失效，请重新使用`srck [cookie]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srsign.finish()
    msg = "签到成功"
    msg_builder = MessageFactory([Text(str(msg))])
    await msg_builder.send(at_sender=True)
    await srsign.finish()


async def geetest_handle(sign_data: dict, cookie: str, role_uid: str = "0"):
    import nonebot
    global_config = nonebot.get_driver().config
    captcha_enable = global_config.captcha_enabled
    logger.debug(captcha_enable)
    if captcha_enable == 0:
        return 1, "请联系管理开启验证码绕过"
    else:
        await srsign.send(f"SRUID{role_uid}正在等待验证码")
    captcha_api_key = global_config.captcha_handler_api_key
    captcha_endpoint = global_config.captcha_handler_api_endpoint
    page_url = "https://webstatic.mihoyo.com/bbs/event/signin/hkrpg/e202304121516551.html"
    gt = sign_data["data"]["gt"]
    challenge = sign_data["data"]["challenge"]
    captcha_result, error_message = await geetest_get_result(api_key=captcha_api_key, api_endpoint=captcha_endpoint,
                                                             gt=gt, challenge=challenge, page_url=page_url)
    if error_message == "":
        return 0, await sign_with_geetest(geetest_challenge=captcha_result["challenge"],
                                          geetest_seccode=captcha_result["seccode"],
                                          geetest_validate=captcha_result["validate"],
                                          cookie=cookie,
                                          role_uid=role_uid)
    else:
        return 1, "解析验证码时出现错误。错误信息" + error_message


async def geetest_get_result(api_key: str,
                             api_endpoint: str,
                             gt: str,
                             challenge: str,
                             page_url: str):
    raise NotImplementedError("请联系管理员开启验证码绕过")


async def sign_with_geetest(geetest_challenge: str,
                            geetest_seccode: str,
                            geetest_validate: str,
                            cookie: str,
                            role_uid: str):
    if (geetest_challenge == "" or geetest_challenge is None
            or geetest_seccode == "" or geetest_seccode is None
            or geetest_validate == "" or geetest_validate is None):
        raise RuntimeError("验证码平台返回数据格式不对，请联系管理员")
    extra_headers = {
        "x-rpc-validate": geetest_validate,
        "x-rpc-challenge": geetest_challenge,
        "x-rpc-seccode": geetest_seccode
    }
    return await mys_api.call_mihoyo_sign(cookie=cookie, role_uid=role_uid, extra_headers=extra_headers)
