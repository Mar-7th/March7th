import contextlib
import hashlib
import json
import random
import string
import time
from typing import Any, Dict, Literal, Optional

import httpx
from nonebot import logger

RECOGNIZE_SERVER = {
    "1": "prod_gf_cn",
    "2": "cn_gf01",
    "5": "cn_qd01",
    # '6': 'os_usa',
    # '7': 'os_euro',
    # '8': 'os_asia',
    # '9': 'os_cht',
}

OLD_URL = "https://api-takumi.mihoyo.com"
NEW_URL = "https://api-takumi-record.mihoyo.com"

# AuthKey
GET_TOKENS_BY_LT_API = (
    f"{OLD_URL}/auth/api/getMultiTokenByLoginTicket"  # 通过login_ticket获取tokens
)
GET_COOKIE_BY_STOKEN_API = (
    f"{OLD_URL}/auth/api/getCookieAccountInfoBySToken"  # 通过stoken获取cookie
)

# 米游社
GAME_RECORD_API = f"{NEW_URL}/game_record/card/wapi/getGameRecordCard"  # 游戏记录

# 崩坏：星穹铁道
STAR_RAIL_ROLE_BASIC_INFO_API = (
    f"{NEW_URL}/game_record/app/hkrpg/api/role/basicInfo"  # 崩坏：星穹铁道角色基础信息
)
STAR_RAIL_INDEX_API = f"{NEW_URL}/game_record/app/hkrpg/api/index"  # 崩坏：星穹铁道角色橱窗信息
STAR_RAIL_AVATAR_INFO_API = (
    f"{NEW_URL}/game_record/app/hkrpg/api/avatar/info"  # 崩坏：星穹铁道角色详细信息
)


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


def generate_headers(cookie, q="", b=None) -> dict:
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
                url=GET_TOKENS_BY_LT_API,
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
                url=GET_COOKIE_BY_STOKEN_API,
                params={"uid": mys_id, "stoken": stoken},
                timeout=10,
            )
            data = data.json()
            return data["data"]["cookie_token"]
    return None


async def call_mihoyo_api(
    api: Literal["game_record", "sr_basic_info", "sr_index", "sr_avatar_info"],
    cookie: str,
    role_uid: str = "0",
    **kwargs,
) -> Optional[Dict]:
    # cookie check
    if not cookie:
        return None
    # request params
    # fill params by api, or keep empty to use default params
    # default params: uid, server_id, role_id
    params: Dict[str, Any] = {}
    params_str: str = ""
    # fill headers and params by api
    if api == "game_record":
        # extra params: mys_id
        mys_id = kwargs.get("mys_id", None)
        if not mys_id:
            raise ValueError("mys_id is required for game_record api")
        url = GAME_RECORD_API  # 游戏记录
        params = {"uid": mys_id}
        params_str = f"uid={mys_id}"
    elif api == "sr_basic_info":
        url = STAR_RAIL_ROLE_BASIC_INFO_API
    elif api == "sr_index":
        url = STAR_RAIL_INDEX_API
    elif api == "sr_avatar_info":
        # extra params: avatar_id
        url = STAR_RAIL_AVATAR_INFO_API
        avatar_id = kwargs.get("avatar_id", None)
        if avatar_id is None:
            raise ValueError("avatar_id is required for sr_avatar_info api")
        server_id = RECOGNIZE_SERVER.get(role_uid[0])
        params = {"id": avatar_id, "need_wiki": "false", "role_id": role_uid, "server": server_id}
        params_str = f"id={avatar_id}&need_wiki=false&role_id={role_uid}&server={server_id}"
    else:  # api not found
        url = None
    if url is not None:  # send request
        # get server_id by role_uid
        server_id = RECOGNIZE_SERVER.get(role_uid[0])
        # fill deault params
        if not params_str:
            params_str = "&".join([f"{k}={v}" for k, v in params.items()])
            params_fixed = f"role_id={role_uid}&server={server_id}"
            params_str = f"{params_str}&{params_fixed}" if params_str else params_fixed
        if not params:
            params = {"role_id": role_uid, "server": server_id}
        # generate headers
        headers = generate_headers(cookie=cookie, q=params_str)
        async with httpx.AsyncClient(headers=headers) as client:
            data = await client.get(
                url=url,
                params=params,
                timeout=10,
            )
    else:  # url is None
        data = None
    # debug log
    # parse data
    try:
        retcode = data.json()["retcode"] if data else None
        if retcode != 0 and data is not None:
            logger.warning(f"mys api ({api}) failed: {data.json()}")
            logger.warning(f"params: {params}")
            data = None
        data = dict(data.json()["data"]) if data else None
    except (json.JSONDecodeError, KeyError):
        data = None
    if data is None:
        logger.warning(f"mys api ({api}) error")
    logger.debug(data)
    return data
