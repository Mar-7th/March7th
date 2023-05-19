import hashlib
import json
import random
import string
import time
import uuid
from typing import Any, Dict, Literal, Optional, Union

import httpx
from nonebot.log import logger

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
PUBLIC_DATA_HOST = "https://public-data-api.mihoyo.com"

# 米游社
GAME_RECORD_API = f"{NEW_URL}/game_record/card/wapi/getGameRecordCard"  # 游戏记录
GET_FP_API = f"{PUBLIC_DATA_HOST}/device-fp/api/getFp"  # device_fp

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


class MysApi:
    device_id: str
    device_fp: str

    async def init_device(self):
        self.device_id = str(uuid.uuid4())
        self.device_fp = await self.get_fp(self.device_id)

    async def generate_headers(
        self, cookie: str, q="", b=None, p=None, r=None
    ) -> Dict[str, str]:
        """
        生成米游社headers
            :param cookie: cookie
            :param q: 查询
            :param b: 请求体
            :param p: x-rpc-page
            :return: headers
        """
        return {
            "DS": self.get_ds(q, b),
            "Origin": "https://webstatic.mihoyo.com",
            "Cookie": cookie,
            "Referer": r if r else "https://webstatic.mihoyo.com/",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS "
            "X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.50.1",
            "X-Rquested-With": "com.mihoyo.hyperion",
            "x-rpc-page": p if p else "",
            "x-rpc-client_type": "5",
            "x-rpc-device_id": self.device_id,
            "x-rpc-device_fp": self.device_fp,
            "x-rpc-app_version": "2.50.1",
        }

    def get_ds(
        self, query: str = "", body: Optional[Dict] = None, mhy_bbs_sign: bool = False
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

    async def get_fp(self, device_id: str):
        headers = {
            "x-rpc-app_version": "2.50.1",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.50.1",
            "x-rpc-client_type": "5",
            "Referer": "https://webstatic.mihoyo.com/",
            "Origin": "https://webstatic.mihoyo.com",
        }
        async with httpx.AsyncClient(headers=headers) as client:
            data = await client.get(
                url=GET_FP_API,
                params={
                    "device_id": device_id,
                    "seed_id": random_hex(16).lower(),
                    "seed_time": str(round(time.time() * 1000)),
                    "platform": "5",
                    "device_fp": random_hex(13).lower(),
                    "app_name": "account_cn",
                    "ext_fields": f"{{\"userAgent\":\"{headers['User-Agent']}\",\"browserScreenSize\":329280,\"maxTouchPoints\":5,\"isTouchSupported\":true,\"browserLanguage\":\"zh-CN\",\"browserPlat\":\"Linux i686\",\"browserTimeZone\":\"Asia/Shanghai\",\"webGlRender\":\"Adreno (TM) 640\",\"webGlVendor\":\"Qualcomm\",\"numOfPlugins\":0,\"listOfPlugins\":\"unknown\",\"screenRatio\":3.75,\"deviceMemory\":\"4\",\"hardwareConcurrency\":\"4\",\"cpuClass\":\"unknown\",\"ifNotTrack\":\"unknown\",\"ifAdBlock\":0,\"hasLiedResolution\":1,\"hasLiedOs\":0,\"hasLiedBrowser\":0}}",
                },
                timeout=10,
            )
            try:
                data = data.json()
                return str(data["data"]["device_fp"])
            except (json.JSONDecodeError, KeyError):
                logger.warning("Failed to get device fp, use random")
                logger.warning(f"Response: {data}")
                return random_hex(13).lower()

    async def get_stoken_by_login_ticket(self, login_ticket: str, mys_id: str):
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

    async def get_cookie_token_by_stoken(self, stoken: str, mys_id: str):
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

    async def get_cookie_by_game_token(self, uid: int, game_token: str):
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

    async def get_stoken_by_game_token(self, uid: int, game_token: str):
        data = {"account_id": uid, "game_token": game_token}
        headers = {
            "DS": self.get_ds(body=data),
            "x-rpc-aigis": "",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-rpc-game_biz": "bbs_cn",
            "x-rpc-sys_version": "11",
            "x-rpc-device_id": self.device_id,
            "x-rpc-device_fp": self.device_fp,
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

    async def create_login_qr(self, app_id: int):
        """
        创建登录二维码
        app_id:
            1-崩坏3, 2-未定事件簿, 4-原神, 5-平台应用, 7-崩坏学园2,
            8-星穹铁道, 9-云游戏, 10-3NNN, 11-PJSH, 12-绝区零, 13-HYG
        """
        params = {"app_id": str(app_id), "device": self.device_id}
        async with httpx.AsyncClient() as client:
            data = await client.get(
                url=CREATE_QRCODE_API,
                params=params,
                timeout=10,
            )
        url = data.json()["data"]["url"]
        ticket = url.split("ticket=")[1]
        ret_data = {
            "app_id": app_id,
            "ticket": ticket,
            "device": self.device_id,
            "url": url,
        }
        return ret_data

    async def check_login_qr(self, login_data: Dict):
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
        self,
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
        page: str = ""
        headers: Dict[str, str] = {}
        refer: str = ""
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
            page = "3.1.3_#/rpg"
        elif api == "sr_index":
            url = STAR_RAIL_INDEX_API
            page = "3.1.3_#/rpg"
        elif api == "sr_avatar_info":
            # extra params: avatar_id
            url = STAR_RAIL_AVATAR_INFO_API
            avatar_id = kwargs.get("avatar_id", None)
            if avatar_id is None:
                raise ValueError("avatar_id is required for sr_avatar_info api")
            server_id = RECOGNIZE_SERVER.get(role_uid[0])
            params = {
                "id": avatar_id,
                "need_wiki": "true",
                "role_id": role_uid,
                "server": server_id,
            }
            params_str = "&".join([f"{k}={v}" for k, v in params.items()])
            page = "3.1.3_#/rpg/role"
            refer = "https://webstatic.mihoyo.com/app/community-game-records/rpg/?bbs_presentation_style=fullscreen"
        elif api == "sr_note":
            url = STAR_RAIL_NOTE_API
            page = "3.1.3_#/rpg"
        elif api == "sr_month_info":
            url = STAR_RAIL_MONTH_INFO_API
            params = {
                "act_id": "e202304121516551",
                "region": RECOGNIZE_SERVER.get(role_uid[0]),
                "uid": role_uid,
                "lang": "zh-cn",
            }
            page = "3.1.3_#/rpg"
        else:  # api not found
            url = None
        if url is not None:  # send request
            # get server_id by role_uid
            server_id = RECOGNIZE_SERVER.get(role_uid[0])
            # fill deault params
            if not params_str:
                params_str = "&".join([f"{k}={v}" for k, v in params.items()])
                params_fixed = f"role_id={role_uid}&server={server_id}"
                params_str = (
                    f"{params_str}&{params_fixed}" if params_str else params_fixed
                )
            if not params:
                params = {"role_id": role_uid, "server": server_id}
            # generate headers
            if not headers:
                headers = await self.generate_headers(
                    cookie=cookie, q=params_str, p=page, r=refer
                )
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
