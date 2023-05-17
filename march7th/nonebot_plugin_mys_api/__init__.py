import hashlib
import json
import random
import string
import time
import uuid
from typing import Any, Dict, Literal, Optional, Union

import httpx
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="MysApi",
    description="米游社API接口",
    usage="",
    extra={
        "version": "1.0",
    },
)

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
HK4_SDK_URL = "https://hk4e-sdk.mihoyo.com"
TAKUMI_HOST = "https://api-takumi.mihoyo.com"
PASSPORT_HOST = "https://passport-api.mihoyo.com"

# AuthKey
GET_TOKENS_BY_LT_API = (
    f"{OLD_URL}/auth/api/getMultiTokenByLoginTicket"  # 通过login_ticket获取tokens
)
GET_COOKIE_BY_STOKEN_API = (
    f"{OLD_URL}/auth/api/getCookieAccountInfoBySToken"  # 通过stoken获取cookie
)
CREATE_QRCODE_API = f"{HK4_SDK_URL}/hk4e_cn/combo/panda/qrcode/fetch"  # 创建登录qrcode
CHECK_QRCODE_API = f"{HK4_SDK_URL}/hk4e_cn/combo/panda/qrcode/query"  # 检查qrcode扫描状态
GET_COOKIE_BY_GAME_TOKEN_API = (
    f"{TAKUMI_HOST}/auth/api/getCookieAccountInfoByGameToken"  # 通过game_token获取cookie
)
GET_STOKEN_BY_GAME_TOKEN_API = f"{PASSPORT_HOST}/account/ma-cn-session/app/getTokenByGameToken"  # 通过game_token获取stoken

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
STAR_RAIL_NOTE_API = f"{NEW_URL}/game_record/app/hkrpg/api/note"  # 崩坏：星穹铁道实时便笺
STAR_RAIL_MONTH_INFO_API = f"{OLD_URL}/event/srledger/month_info"  # 崩坏：星穹铁道开拓月历


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


def get_ds(
    query: str = "", body: Optional[Dict] = None, mhy_bbs_sign: bool = False
) -> str:
    """
    生成米游社headers的ds_token

    :param query: 查询
    :param body: 请求体
    :param mhy_bbs_sign: 是否为米游社讨论区签到
    :return: ds_token
    """
    b = json.dumps(body) if body else ""
    if mhy_bbs_sign:
        s = "t0qEgfub6cvueAPgR5m9aQWWVciEer7v"
    else:
        s = "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs"
    t = str(int(time.time()))
    r = str(random.randint(100000, 200000))
    c = md5(f"salt={s}&t={t}&r={r}&b={b}&q={query}")
    return f"{t},{r},{c}"


def generate_headers(cookie: str, q="", b=None) -> Dict[str, str]:
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
        "Referer": "https://webstatic.mihoyo.com/",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS "
        "X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.50.1",
        "X-Rquested-With": "com.mihoyo.hyperion",
        "x-rpc-client_type": "5",
        "x-rpc-device_id": uuid.uuid4().hex,
        "x-rpc-device_fp": "".join(
            random.choices((string.ascii_letters + string.digits), k=13)
        ),
        "x-rpc-app_version": "2.50.1",
    }


async def get_stoken_by_login_ticket(login_ticket: str, mys_id: str):
    async with httpx.AsyncClient(
        headers={
            "x-rpc-app_version": "2.50.1",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.50.1",
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
        try:
            data = data.json()
            return data["data"]["list"][0]["token"]
        except (json.JSONDecodeError, KeyError):
            return None


async def get_cookie_token_by_stoken(stoken: str, mys_id: str):
    async with httpx.AsyncClient(
        headers={
            "x-rpc-app_version": "2.50.1",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.50.1",
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
        try:
            data = data.json()
            return data["data"]["cookie_token"]
        except (json.JSONDecodeError, KeyError):
            return None


async def get_cookie_by_game_token(uid: int, game_token: str):
    async with httpx.AsyncClient() as client:
        data = await client.get(
            url=GET_COOKIE_BY_GAME_TOKEN_API,
            params={"game_token": game_token, "account_id": uid},
            timeout=10,
        )
        try:
            return data.json()
        except json.JSONDecodeError:
            return None


async def get_stoken_by_game_token(uid: int, game_token: str):
    data = {"account_id": uid, "game_token": game_token}
    headers = {
        "DS": get_ds(body=data),
        "x-rpc-aigis": "",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-rpc-game_biz": "bbs_cn",
        "x-rpc-sys_version": "11",
        "x-rpc-device_id": uuid.uuid4().hex,
        "x-rpc-device_fp": "".join(
            random.choices((string.ascii_letters + string.digits), k=13)
        ),
        "x-rpc-device_name": "Chrome 108.0.0.0",
        "x-rpc-device_model": "Windows 10 64-bit",
        "x-rpc-app_id": "bll8iq97cem8",
        "User-Agent": "okhttp/4.8.0",
    }
    async with httpx.AsyncClient(headers=headers) as client:
        data = await client.post(
            url=GET_STOKEN_BY_GAME_TOKEN_API,
            params=data,
            timeout=10,
        )
        try:
            return data.json()
        except json.JSONDecodeError:
            return None


async def create_login_qr(app_id: int):
    """
    创建登录二维码
    app_id:
        1-崩坏3, 2-未定事件簿, 4-原神, 5-平台应用, 7-崩坏学园2,
        8-星穹铁道, 9-云游戏, 10-3NNN, 11-PJSH, 12-绝区零, 13-HYG
    """
    device_id = "".join(random.choices((string.ascii_letters + string.digits), k=64))
    params = {"app_id": str(app_id), "device": device_id}
    async with httpx.AsyncClient() as client:
        data = await client.get(
            url=CREATE_QRCODE_API,
            params=params,
            timeout=10,
        )
    url = data.json()["data"]["url"]
    ticket = url.split("ticket=")[1]
    ret_data = {"app_id": app_id, "ticket": ticket, "device": device_id, "url": url}
    return ret_data


async def check_login_qr(login_data: Dict):
    params = {
        "app_id": login_data["app_id"],
        "ticket": login_data["ticket"],
        "device": login_data["device"],
    }
    async with httpx.AsyncClient() as client:
        data = await client.get(
            url=CHECK_QRCODE_API,
            params=params,
            timeout=10,
        )
    return data.json()


async def call_mihoyo_api(
    api: Literal[
        "game_record",
        "sr_basic_info",
        "sr_index",
        "sr_avatar_info",
        "sr_note",
        "sr_month_info",
    ],
    cookie: str,
    role_uid: str = "0",
    **kwargs,
) -> Union[Dict, int, None]:
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
        params = {
            "id": avatar_id,
            "need_wiki": "false",
            "role_id": role_uid,
            "server": server_id,
        }
        params_str = (
            f"id={avatar_id}&need_wiki=false&role_id={role_uid}&server={server_id}"
        )
    elif api == "sr_note":
        url = STAR_RAIL_NOTE_API
    elif api == "sr_month_info":
        url = STAR_RAIL_MONTH_INFO_API
        params = {
            "act_id": "e202304121516551",
            "region": RECOGNIZE_SERVER.get(role_uid[0]),
            "uid": role_uid,
            "lang": "zh-cn",
        }
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
    if data is not None:
        try:
            retcode = int(data.json()["retcode"])
            if retcode != 0:
                logger.warning(f"mys api ({api}) failed: {data.json()}")
                logger.warning(f"params: {params}")
                data = retcode
            else:
                data = dict(data.json()["data"])
        except (json.JSONDecodeError, KeyError):
            data = None
    if data is None:
        logger.warning(f"mys api ({api}) error")
    logger.debug(data)
    return data
