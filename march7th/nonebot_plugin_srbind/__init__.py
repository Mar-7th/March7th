import re

from nonebot import on_command, require
from nonebot.adapters import Bot, Event, Message
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_datastore")
require("nonebot_plugin_saa")
require("nonebot_plugin_mys_api")

from nonebot_plugin_saa import MessageFactory, Text

try:
    from march7th.nonebot_plugin_mys_api import (
        get_bind_game_info,
        get_cookie_token_by_stoken,
        get_stoken_by_login_ticket,
    )
except ModuleNotFoundError:
    from nonebot_plugin_mys_api import (
        get_stoken_by_login_ticket,
        get_cookie_token_by_stoken,
        get_bind_game_info,
    )

from .models import UserBind, del_user_srbind, get_user_srbind, set_user_srbind

__plugin_meta__ = PluginMetadata(
    name="StarRailBind",
    description="崩坏：星穹铁道账号绑定",
    usage="sruid / sruid [UID] / srdel / srck [COOKIE] / srdel [UID]",
    extra={
        "version": "1.0",
    },
)

sruid = on_command("sruid", aliases={"星铁uid", "星铁绑定", "星铁账号绑定"}, priority=2, block=True)
srck = on_command(
    "srck", aliases={"星铁ck", "srcookie", "星铁cookie"}, priority=2, block=True
)
srpck = on_command(
    "srpck",
    aliases={"星铁pck", "srpcookie", "星铁公共cookie"},
    permission=SUPERUSER,
    priority=2,
    block=True,
)
srdel = on_command(
    "srdel",
    aliases={"星铁解绑", "星铁取消绑定", "星铁解除绑定", "星铁取消账号绑定", "星铁解除账号绑定"},
    priority=2,
    block=True,
)


@sruid.handle()
async def _(bot: Bot, event: Event, arg: Message = CommandArg()):
    sr_uid: str = arg.extract_plain_text().strip()
    if not sr_uid:
        logger.info(f"开始查询『{event.get_user_id()}』的SRUID绑定状态")
        uaer_list = await get_user_srbind(bot.self_id, event.get_user_id())
        if uaer_list:
            uid_list_str = [str(user.sr_uid) for user in uaer_list]
            msg = "已绑定SRUID：\n" + "\n".join(uid_list_str)
        else:
            msg = "未绑定SRUID"
    else:
        uid = re.match(r"[1]\d{8}", sr_uid)
        if not uid:
            msg = "SRUID格式错误"
        else:
            logger.info(f"开始为『{event.get_user_id()}』绑定SRUID『{sr_uid}』")
            user = UserBind(
                bot_id=bot.self_id,
                user_id=str(event.get_user_id()),
                sr_uid=sr_uid,
            )
            await set_user_srbind(user)
            msg = f"成功绑定SRUID『{sr_uid}』"
    msg_builder = MessageFactory([Text(str(msg))])
    await msg_builder.send(at_sender=True)
    await sruid.finish()


@srck.handle()
async def _(bot: Bot, event: Event, arg: Message = CommandArg()):
    cookie: str = arg.extract_plain_text().strip()
    if cookie in {"cookie", "[cookie]", "Cookie", "[COOKIE]", "ck", "CK", ""}:
        msg = f"请查看教程获取cookie:\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1"
    if not (
        mys_id := re.search(
            r"(?:(?:login_uid|account_mid|account_id|stmid|ltmid|stuid|ltuid)(?:_v2)?)=(\d+)",
            cookie,
        )
    ):
        msg = "cookie无效，缺少account_id、login_uid或stuid字段\n获取cookie的教程:\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1"
    else:
        mys_id = mys_id[1]
        cookie_token_match = re.search(
            r"(?:cookie_token|cookie_token_v2)=([0-9a-zA-Z]+)", cookie
        )
        cookie_token = cookie_token_match[1] if cookie_token_match else None
        login_ticket_match = re.search(
            r"(?:login_ticket|login_ticket_v2)=([0-9a-zA-Z]+)", cookie
        )
        login_ticket = login_ticket_match[1] if login_ticket_match else None
        stoken_match = re.search(r"(?:stoken|stoken_v2)=([0-9a-zA-Z]+)", cookie)
        stoken = stoken_match[1] if stoken_match else None
        logger.debug(f"login_ticket: {login_ticket}")
        if login_ticket and not stoken:
            # 如果有login_ticket但没有stoken，就通过login_ticket获取stoken
            stoken = await get_stoken_by_login_ticket(login_ticket, mys_id)
            logger.debug(f"stoken: {stoken}")
        if stoken and not cookie_token:
            # 如果有stoken但没有cookie_token，就通过stoken获取cookie_token
            cookie_token = await get_cookie_token_by_stoken(stoken, mys_id)
            logger.debug(f"cookie_token: {cookie_token}")
        if not cookie_token:
            msg = "cookie无效，缺少cookie_token或login_ticket字段\n获取cookie的教程：\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1"
        elif game_info := await get_bind_game_info(
            f"account_id={mys_id};cookie_token={cookie_token}", mys_id
        ):
            if not game_info["list"]:
                msg = "该账号尚未绑定任何游戏，请确认账号无误~"
            elif not (
                sr_games := [
                    {"uid": game["game_role_id"], "nickname": game["nickname"]}
                    for game in game_info["list"]
                    if game["game_id"] == 6
                ]
            ):
                msg = "该账号尚未绑定星穹铁道，请确认账号无误~"
            else:
                player = ""
                for info in sr_games:
                    player += f'{info["nickname"]}({info["uid"]}) '
                    user = UserBind(
                        bot_id=bot.self_id,
                        user_id=str(event.get_user_id()),
                        mys_id=mys_id,
                        sr_uid=info["uid"],
                        cookie=f"account_id={mys_id};cookie_token={cookie_token}",
                        stoken=f"stuid={mys_id};stoken={stoken};" if stoken else None,
                    )
                    await set_user_srbind(user)
                msg = f'玩家{player.strip()}绑定cookie{"和stoken" if stoken else ""}成功{"" if stoken else "当未能绑定stoken"}，建议将cookie撤回哦"'
        else:
            msg = "Cookie无效，请确认是否已过期\n获取cookie的教程：\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1"
    msg_builder = MessageFactory([Text(str(msg))])
    await msg_builder.send(at_sender=True)
    await srck.finish()


@srpck.handle()
async def _(bot: Bot, event: Event, arg: Message = CommandArg()):
    cookie: str = arg.extract_plain_text().strip()
    if cookie in {"cookie", "[cookie]", "Cookie", "[COOKIE]", "ck", "CK", ""}:
        msg = f"请查看教程获取cookie:\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1"
    if not (
        mys_id := re.search(
            r"(?:(?:login_uid|account_mid|account_id|stmid|ltmid|stuid|ltuid)(?:_v2)?)=(\d+)",
            cookie,
        )
    ):
        msg = "cookie无效，缺少account_id、login_uid或stuid字段\n获取cookie的教程:\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1"
    else:
        mys_id = mys_id[1]
        cookie_token_match = re.search(
            r"(?:cookie_token|cookie_token_v2)=([0-9a-zA-Z]+)", cookie
        )
        cookie_token = cookie_token_match[1] if cookie_token_match else None
        login_ticket_match = re.search(
            r"(?:login_ticket|login_ticket_v2)=([0-9a-zA-Z]+)", cookie
        )
        login_ticket = login_ticket_match[1] if login_ticket_match else None
        stoken_match = re.search(r"(?:stoken|stoken_v2)=([0-9a-zA-Z]+)", cookie)
        stoken = stoken_match[1] if stoken_match else None
        logger.debug(f"login_ticket: {login_ticket}")
        if login_ticket and not stoken:
            # 如果有login_ticket但没有stoken，就通过login_ticket获取stoken
            stoken = await get_stoken_by_login_ticket(login_ticket, mys_id)
            logger.debug(f"stoken: {stoken}")
        if stoken and not cookie_token:
            # 如果有stoken但没有cookie_token，就通过stoken获取cookie_token
            cookie_token = await get_cookie_token_by_stoken(stoken, mys_id)
            logger.debug(f"cookie_token: {cookie_token}")
        if not cookie_token:
            msg = "cookie无效，缺少cookie_token或login_ticket字段\n获取cookie的教程：\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1"
        else:
            user = UserBind(
                bot_id=bot.self_id,
                user_id="0",
                mys_id=mys_id,
                sr_uid="0",
                cookie=f"account_id={mys_id};cookie_token={cookie_token}",
                stoken=f"stuid={mys_id};stoken={stoken};" if stoken else None,
            )
            await set_user_srbind(user)
            msg = f"绑定公共cookie成功"
    msg_builder = MessageFactory([Text(str(msg))])
    await msg_builder.send(at_sender=True)
    await srpck.finish()


@srdel.handle()
async def _(bot: Bot, event: Event, arg: Message = CommandArg()):
    sr_uid: str = arg.extract_plain_text().strip()
    if not sr_uid:
        logger.info(f"开始解绑『{event.get_user_id()}』的所有SRUID")
        user_list = await get_user_srbind(bot.self_id, event.get_user_id())
        if user_list:
            uid_list_str = [user.sr_uid for user in user_list]
            for uid in uid_list_str:
                await del_user_srbind(bot.self_id, event.get_user_id(), uid)
            msg = "已解绑SRUID：\n" + "\n".join(uid_list_str)
        else:
            msg = "未绑定SRUID"
    else:
        uid = re.match(r"[1]\d{8}", sr_uid)
        if not uid:
            msg = "SRUID格式错误"
        else:
            sr_uid = uid.group()
            uid_list = await get_user_srbind(bot.self_id, event.get_user_id())
            if uid_list:
                if sr_uid in uid_list:
                    logger.info(f"开始为『{event.get_user_id()}』解绑SRUID『{sr_uid}』")
                    await del_user_srbind(bot.self_id, event.get_user_id(), sr_uid)
                    msg = f"已解绑SRUID『{sr_uid}』"
                else:
                    msg = f"未绑定SRUID『{sr_uid}』"
            else:
                msg = "未绑定SRUID"
    msg_builder = MessageFactory([Text(str(msg))])
    await msg_builder.send(at_sender=True)
    await srdel.finish()
