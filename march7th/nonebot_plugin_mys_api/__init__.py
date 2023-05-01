import contextlib
import hashlib
import json
import random
import string
import time
from typing import Literal, Optional

import httpx
from nonebot import logger

RECOGNIZE_SERVER = {
    "1": "prod_gf_cn",
}

OLD_URL = "https://api-takumi.mihoyo.com"
NEW_URL = "https://api-takumi-record.mihoyo.com"

GAME_RECORD_API = f"{NEW_URL}/game_record/card/wapi/getGameRecordCard"  # 游戏记录卡片接口
STOKEN_API = f"{OLD_URL}/auth/api/getMultiTokenByLoginTicket"  # stoken接口
COOKIE_TOKEN_API = f"{OLD_URL}/auth/api/getCookieAccountInfoBySToken"  # cookie_token接口

STAR_RAIL_ROLE_BASIC_INFO_URL = (
    f"{NEW_URL}/game_record/app/hkrpg/api/role/basicInfo"  # 角色基础信息接口
)
STAR_RAIL_INDEX_URL = f"{NEW_URL}/game_record/app/hkrpg/api/index"  # 角色橱窗信息接口


def md5(text: str) -> str:
    """
    md5
    """
    md5_ = hashlib.md5()
    md5_.update(text.encode())
    return md5_.hexdigest()


def random_hex(length: int) -> str:
    """
    生成指定长度的随机16进制字符串
    """
    result = hex(random.randint(0, 16**length)).replace("0x", "").upper()
    if len(result) < length:
        result = "0" * (length - len(result)) + result
    return result


def random_text(length: int) -> str:
    """
    生成指定长度的随机字符串
    """
    return "".join(random.sample(string.ascii_lowercase + string.digits, length))


def get_ds(q: str = "", b: Optional[dict] = None, mhy_bbs_sign: bool = False) -> str:
    """
    生成米游社headers的ds_token

    :param q: 查询
    :param b: 请求体
    :param mhy_bbs_sign: 是否为米游社讨论区签到
    :return: ds_token
    """
    br = json.dumps(b) if b else ""
    if mhy_bbs_sign:
        s = "t0qEgfub6cvueAPgR5m9aQWWVciEer7v"
    else:
        s = "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs"
    t = str(int(time.time()))
    r = str(random.randint(100000, 200000))
    c = md5(f"salt={s}&t={t}&r={r}&b={br}&q={q}")
    return f"{t},{r},{c}"


def mihoyo_headers(cookie, q="", b=None) -> dict:
    """
    生成米游社headers
        :param cookie: cookie
        :param q: 查询
        :param b: 请求体
        :return: headers
    """
    return {
        "DS": get_ds(q, b),
        "Origin": "https://webstatic.mihoyo.com",
        "Cookie": cookie,
        "x-rpc-app_version": "2.11.1",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS "
        "X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1",
        "x-rpc-client_type": "5",
        "Referer": "https://webstatic.mihoyo.com/",
    }


async def get_bind_game_info(cookie: str, mys_id: str):
    """
    通过cookie，获取米游社绑定的原神游戏信息
    :param cookie: cookie
    :param mys_id: 米游社id
    :return: 原神信息
    """
    with contextlib.suppress(Exception):
        async with httpx.AsyncClient(
            headers=mihoyo_headers(cookie, f"uid={mys_id}")
        ) as client:
            data = await client.get(
                url=GAME_RECORD_API, params={"uid": mys_id}, timeout=10
            )
            data = data.json()
            logger.debug(data)
            if data["retcode"] == 0:
                return data["data"]
    return None


async def get_stoken_by_login_ticket(login_ticket: str, mys_id: str) -> Optional[str]:
    with contextlib.suppress(Exception):
        async with httpx.AsyncClient(
            headers={
                "x-rpc-app_version": "2.11.2",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1",
                "x-rpc-client_type": "5",
                "Referer": "https://webstatic.mihoyo.com/",
                "Origin": "https://webstatic.mihoyo.com",
            }
        ) as client:
            data = await client.get(
                url=STOKEN_API,
                params={
                    "login_ticket": login_ticket,
                    "token_types": "3",
                    "uid": mys_id,
                },
                timeout=10,
            )
            data = data.json()
            return data["data"]["list"][0]["token"]
    return None


async def get_cookie_token_by_stoken(stoken: str, mys_id: str) -> Optional[str]:
    with contextlib.suppress(Exception):
        async with httpx.AsyncClient(
            headers={
                "x-rpc-app_version": "2.11.2",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1",
                "x-rpc-client_type": "5",
                "Referer": "https://webstatic.mihoyo.com/",
                "Origin": "https://webstatic.mihoyo.com",
                "Cookie": f"stuid={mys_id};stoken={stoken}",
            }
        ) as client:
            data = await client.get(
                url=COOKIE_TOKEN_API,
                params={"uid": mys_id, "stoken": stoken},
                timeout=10,
            )
            data = data.json()
            return data["data"]["cookie_token"]
    return None


async def get_mihoyo_public_data(
    uid: str,
    cookie: str,
    mode: Literal["sr_basic_info", "sr_index"],
):
    server_id = RECOGNIZE_SERVER.get(uid[0])
    if not cookie:
        return None
    headers = mihoyo_headers(q=f"role_id={uid}&server={server_id}", cookie=cookie)
    if mode == "sr_basic_info":
        url = STAR_RAIL_ROLE_BASIC_INFO_URL
    elif mode == "sr_index":
        url = STAR_RAIL_INDEX_URL
    else:
        url = None
    if url:
        async with httpx.AsyncClient(headers=headers) as client:
            data = await client.get(
                url=url,
                params={"role_id": uid, "server": server_id},
                timeout=10,
            )
    else:
        data = None
    data = dict(data.json()) if data else {"retcode": 999}
    logger.debug(data)
    return data
