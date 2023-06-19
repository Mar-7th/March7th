import random
from typing import Optional

from .models import get_user_srbind, set_user_srbind


async def get_user_cookie(
    bot_id: str, user_id: str, sr_uid: Optional[str]
) -> Optional[str]:
    select_user = await get_user_srbind(bot_id, user_id)
    select_uid = [user.sr_uid for user in select_user]
    if not select_uid:
        return None
    if sr_uid in select_uid:
        user = select_user[select_uid.index(sr_uid)]
        return user.cookie
    else:
        user = select_user[0]
        return user.cookie


async def get_user_stoken(
    bot_id: str, user_id: str, sr_uid: Optional[str]
) -> Optional[str]:
    select_user = await get_user_srbind(bot_id, user_id)
    select_uid = [user.sr_uid for user in select_user]
    if not select_uid:
        return None
    if sr_uid in select_uid:
        user = select_user[select_uid.index(sr_uid)]
        return user.stoken
    else:
        user = select_user[0]
        return user.stoken


async def get_public_cookie(bot_id: str) -> Optional[str]:
    select_user = await get_user_srbind(bot_id, "0")
    if not select_user:
        return None
    cookies = [user.cookie for user in select_user if user.cookie]
    cookie = random.choice(cookies)
    return cookie


async def set_cookie_expire(bot_id: str, user_id: str, sr_uid: str):
    select_user = await get_user_srbind(bot_id, user_id)
    select_uid = [user.sr_uid for user in select_user]
    if sr_uid in select_uid:
        user = select_user[select_uid.index(sr_uid)]
        user.cookie = None
        await set_user_srbind(user)
