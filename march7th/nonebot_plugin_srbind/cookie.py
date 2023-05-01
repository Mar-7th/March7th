from typing import Optional

from .models import get_user_srbind


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
