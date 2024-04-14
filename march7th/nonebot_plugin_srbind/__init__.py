import re
import json
import asyncio
import contextlib
from io import BytesIO
from typing import Any, Dict

from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot import get_bot, require, on_command
from nonebot.adapters import Bot, Event, Message

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_datastore")
require("nonebot_plugin_saa")
require("nonebot_plugin_mys_api")

from nonebot_plugin_apscheduler import scheduler
from nonebot_plugin_saa import (
    Text,
    Image,
    Mention,
    MessageFactory,
    PlatformTarget,
    extract_target,
)

try:
    from march7th.nonebot_plugin_mys_api import MysApi
except ModuleNotFoundError:
    from nonebot_plugin_mys_api import MysApi

from .model import UserBind
from .data_source import (
    del_user_srbind,
    generate_qrcode,
    get_user_srbind,
    set_user_srbind,
)

__plugin_meta__ = PluginMetadata(
    name="StarRailBind",
    description="崩坏：星穹铁道账号绑定",
    usage="""\
查看绑定: sruid
绑定UID: sruid [UID]
清空绑定: srdel
删除UID: srdel [UID]
绑定cookie: srck  [COOKIE]
扫码绑定: srqr
""",
    extra={
        "version": "1.0",
        "srhelp": """\
查看绑定: sruid
绑定UID: sruid [u]UID[/u]
清空绑定: srdel
删除UID: srdel [u]UID[/u]
绑定cookie: srck [u]COOKIE[/u]
扫码绑定: srqr
""",
    },
)

qrbind_buffer: Dict[str, Any] = {}

sruid = on_command(
    "sruid", aliases={"星铁uid", "星铁绑定", "星铁账号绑定"}, priority=2, block=True
)
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
    aliases={
        "星铁解绑",
        "星铁取消绑定",
        "星铁解除绑定",
        "星铁取消账号绑定",
        "星铁解除账号绑定",
    },
    priority=2,
    block=True,
)
srqr = on_command(
    "srqr",
    aliases={"星铁扫码绑定"},
    priority=2,
    block=True,
)


@sruid.handle()
async def _(bot: Bot, event: Event, arg: Message = CommandArg()):
    sr_uid: str = arg.extract_plain_text().strip()
    if not sr_uid:
        logger.info(f"开始查询『{event.get_user_id()}』的SRUID绑定状态")
        user_list = await get_user_srbind(bot.self_id, event.get_user_id())
        if user_list:
            uid_list_str = [str(user.sr_uid) for user in user_list]
            msg = "已绑定SRUID：\n" + "\n".join(uid_list_str)
        else:
            msg = "未绑定SRUID"
    else:
        uid = re.match(r"[1]\d{8}$", sr_uid)
        if not uid:
            msg = "SRUID格式错误"
        else:
            logger.info(f"开始为『{event.get_user_id()}』绑定SRUID『{uid.group()}』")
            user = UserBind(
                bot_id=bot.self_id,
                user_id=str(event.get_user_id()),
                sr_uid=uid.group(),
            )
            await set_user_srbind(user)
            msg = f"成功绑定SRUID『{uid.group()}』"
    msg_builder = MessageFactory([Text(str(msg))])
    await msg_builder.finish(at_sender=not event.is_tome())


@srck.handle()
async def _(bot: Bot, event: Event, arg: Message = CommandArg()):
    cookie: str = arg.extract_plain_text().strip()
    if cookie in {"cookie", "[cookie]", "Cookie", "[COOKIE]", "ck", "CK", ""}:
        msg = "请查看教程获取cookie:\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1"
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
        mys_api = MysApi()
        if login_ticket and not stoken:
            # 如果有login_ticket但没有stoken，就通过login_ticket获取stoken
            stoken = await mys_api.get_stoken_by_login_ticket(login_ticket, mys_id)
            logger.debug(f"stoken: {stoken}")
        if stoken and not cookie_token:
            # 如果有stoken但没有cookie_token，就通过stoken获取cookie_token
            cookie_token = await mys_api.get_cookie_token_by_stoken(stoken, mys_id)
            logger.debug(f"cookie_token: {cookie_token}")
        mys_api = MysApi(cookie=f"account_id={mys_id};cookie_token={cookie_token}")
        if not cookie_token:
            msg = "cookie无效，缺少cookie_token或login_ticket字段\n获取cookie的教程：\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1"
        elif game_info := await mys_api.call_mihoyo_api(
            api="game_record",
            mys_id=mys_id,
        ):
            if isinstance(game_info, int):
                msg = f"绑定失败，请稍后重试（错误代码 {game_info}）"
            elif not game_info["list"]:
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
                    device_id, device_fp = await mys_api.init_device()
                    user = UserBind(
                        bot_id=bot.self_id,
                        user_id=str(event.get_user_id()),
                        mys_id=mys_id,
                        sr_uid=info["uid"],
                        device_id=device_id,
                        device_fp=device_fp,
                        cookie=f"account_id={mys_id};cookie_token={cookie_token}",
                        stoken=f"stuid={mys_id};stoken={stoken};" if stoken else None,
                    )
                    await set_user_srbind(user)
                msg = f'玩家{player.strip()}绑定cookie{"和stoken" if stoken else ""}成功{"" if stoken else "当未能绑定stoken"}，建议将cookie撤回哦'
        else:
            msg = "Cookie无效，请确认是否已过期\n获取cookie的教程：\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1"
    msg_builder = MessageFactory([Text(str(msg))])
    await msg_builder.finish(at_sender=not event.is_tome())


@srpck.handle()
async def _(bot: Bot, event: Event, arg: Message = CommandArg()):
    cookie: str = arg.extract_plain_text().strip()
    if cookie in {"cookie", "[cookie]", "Cookie", "[COOKIE]", "ck", "CK", ""}:
        msg = "请查看教程获取cookie:\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1"
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
        mys_api = MysApi()
        if login_ticket and not stoken:
            # 如果有login_ticket但没有stoken，就通过login_ticket获取stoken
            stoken = await mys_api.get_stoken_by_login_ticket(login_ticket, mys_id)
            logger.debug(f"stoken: {stoken}")
        if stoken and not cookie_token:
            # 如果有stoken但没有cookie_token，就通过stoken获取cookie_token
            cookie_token = await mys_api.get_cookie_token_by_stoken(stoken, mys_id)
            logger.debug(f"cookie_token: {cookie_token}")
        if not cookie_token:
            msg = "cookie无效，缺少cookie_token或login_ticket字段\n获取cookie的教程：\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1"
        else:
            device_id, device_fp = await mys_api.init_device()
            user = UserBind(
                bot_id=bot.self_id,
                user_id="0",
                mys_id=mys_id,
                sr_uid="0",
                device_id=device_id,
                device_fp=device_fp,
                cookie=f"account_id={mys_id};cookie_token={cookie_token}",
                stoken=f"stuid={mys_id};stoken={stoken};" if stoken else None,
            )
            await set_user_srbind(user)
            msg = "绑定公共cookie成功"
    msg_builder = MessageFactory([Text(str(msg))])
    await msg_builder.finish(at_sender=not event.is_tome())


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
    await msg_builder.finish(at_sender=not event.is_tome())


@srqr.handle()
async def _(bot: Bot, event: Event):
    user_id = str(event.get_user_id())
    if user_id in qrbind_buffer:
        msg_builder = MessageFactory([Text("你已经在绑定中了，请扫描上一次的二维码")])
        await msg_builder.finish(at_sender=not event.is_tome())
    mys_api = MysApi()
    login_data = await mys_api.create_login_qr(8)
    if login_data is None:
        msg_builder = MessageFactory(
            [
                Mention(user_id),
                Text("生成二维码失败，请稍后重试"),
            ]
        )
        await msg_builder.finish()
    qr_img: BytesIO = generate_qrcode(login_data["url"])
    qrbind_buffer[user_id] = login_data
    qrbind_buffer[user_id]["bot_id"] = bot.self_id
    qrbind_buffer[user_id]["qr_img"] = qr_img
    qrbind_buffer[user_id]["target"] = extract_target(event).json()
    msg_builder = MessageFactory(
        [
            Image(qr_img),
            Text("\n"),
            Mention(user_id),
            Text(
                "\n请在3分钟内使用米游社扫码并确认进行绑定。\n注意：1.扫码即代表你同意将cookie信息授权给Bot使用\n2.扫码时会提示登录游戏，但不会挤掉账号\n3.其他人请不要乱扫，否则会将你的账号绑到TA身上！"
            ),
        ]
    )
    await msg_builder.finish()


@scheduler.scheduled_job("cron", second="*/10", misfire_grace_time=10)
async def check_qrcode():
    with contextlib.suppress(RuntimeError):
        for user_id, data in qrbind_buffer.items():
            logger.debug(f"Check qr result of {user_id}")
            try:
                mys_api = MysApi()
                status_data = await mys_api.check_login_qr(data)
                if status_data is None:
                    logger.warning(f"Check of user_id {user_id} failed")
                    msg_builder = MessageFactory(
                        [
                            Mention(user_id),
                            Text("绑定二维码已失效，请重新发送扫码绑定指令"),
                        ]
                    )
                    target = PlatformTarget.deserialize(data["target"])
                    bot = get_bot(self_id=data["bot_id"])
                    await msg_builder.send_to(target=target, bot=bot)
                    qrbind_buffer.pop(user_id)
                    continue
                logger.debug(status_data)
                if status_data["retcode"] != 0:
                    logger.debug(f"QR code of user_id {user_id} expired")
                    qrbind_buffer.pop(user_id)
                    msg_builder = MessageFactory(
                        [
                            Mention(user_id),
                            Text("绑定二维码已过期，请重新发送扫码绑定指令"),
                        ]
                    )
                    target = PlatformTarget.deserialize(data["target"])
                    bot = get_bot(self_id=data["bot_id"])
                    await msg_builder.send_to(target=target, bot=bot)
                    qrbind_buffer.pop(user_id)
                    continue
                if status_data["data"]["stat"] != "Confirmed":
                    continue
                logger.debug(f"QR code of user_id {user_id} confirmed")
                game_token = json.loads(status_data["data"]["payload"]["raw"])
                cookie_data = await mys_api.get_cookie_by_game_token(
                    int(game_token["uid"]), game_token["token"]
                )
                stoken_data = await mys_api.get_stoken_by_game_token(
                    int(game_token["uid"]), game_token["token"]
                )
                if not cookie_data or not stoken_data:
                    logger.debug(f"Get cookie and stoken failed of user_id {user_id}")
                    msg_builder = MessageFactory(
                        [
                            Mention(user_id),
                            Text("获取cookie失败，请稍后重试"),
                        ]
                    )
                    target = PlatformTarget.deserialize(data["target"])
                    bot = get_bot(self_id=data["bot_id"])
                    await msg_builder.send_to(target=target, bot=bot)
                    qrbind_buffer.pop(user_id)
                    continue
                mys_id = stoken_data["data"]["user_info"]["aid"]
                mid = stoken_data["data"]["user_info"]["mid"]
                cookie_token = cookie_data["data"]["cookie_token"]
                stoken = stoken_data["data"]["token"]["token"]
                device_id = qrbind_buffer[user_id]["device"]
                device_id, device_fp = await mys_api.init_device(device_id)
                mys_api = MysApi(
                    cookie=f"account_id={mys_id};cookie_token={cookie_token}",
                    device_id=device_id,
                    device_fp=device_fp,
                )
                game_info = await mys_api.call_mihoyo_api(
                    api="game_record",
                    mys_id=mys_id,
                )
                logger.debug(f"Game info: {game_info}")
                if game_info is None:
                    msg_builder = MessageFactory(
                        [
                            Mention(user_id),
                            Text("获取游戏信息失败，请稍后重试"),
                        ]
                    )
                    logger.debug(f"Get game record failed of user_id {user_id}")
                elif isinstance(game_info, int):
                    msg_builder = MessageFactory(
                        [
                            Mention(user_id),
                            Text(f"绑定失败，请稍后重试（错误代码 {game_info}）"),
                        ]
                    )
                    logger.debug(f"Get game record failed of user_id {user_id}")
                elif not game_info["list"]:
                    msg_builder = MessageFactory(
                        [
                            Mention(user_id),
                            Text("该账号尚未绑定任何游戏，请确认扫码的账号无误"),
                        ]
                    )
                    logger.debug(f"No game record of user_id {user_id}")
                elif not (
                    sr_games := [
                        {
                            "uid": game["game_role_id"],
                            "nickname": game["nickname"],
                        }
                        for game in game_info["list"]
                        if game["game_id"] == 6
                    ]
                ):
                    msg_builder = MessageFactory(
                        [
                            Mention(user_id),
                            Text("该账号尚未绑定星穹铁道，请确认扫码的账号无误"),
                        ]
                    )
                    logger.debug(f"No hsr game record of user_id {user_id}")
                else:
                    logger.debug(f"Found game record of user_id {user_id}: {sr_games}")
                    msg_builder = MessageFactory(
                        [Mention(user_id), Text("成功绑定星穹铁道账号:\n")]
                    )
                    for info in sr_games:
                        msg_builder += MessageFactory(
                            [Text(f"{info['nickname']} ({info['uid']})")]
                        )
                        user = UserBind(
                            bot_id=data["bot_id"],
                            user_id=str(user_id),
                            mys_id=mys_id,
                            sr_uid=info["uid"],
                            device_id=device_id,
                            device_fp=device_fp,
                            cookie=f"account_id={mys_id};cookie_token={cookie_token}",
                            stoken=(
                                f"stuid={mys_id};stoken={stoken};mid={mid};"
                                if stoken
                                else None
                            ),
                        )
                        await set_user_srbind(user)
                # send message to origin target
                target = PlatformTarget.deserialize(data["target"])
                bot = get_bot(self_id=data["bot_id"])
                await msg_builder.send_to(target=target, bot=bot)
                qrbind_buffer.pop(user_id)
                logger.debug(f"Check of user_id {user_id} success")
                if not qrbind_buffer:
                    break
            except Exception as e:
                logger.warning(f"QR process error: {e}")
                logger.exception(e)
            finally:
                await asyncio.sleep(1)
