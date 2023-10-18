from io import BytesIO
from typing import List

import qrcode
from nonebot_plugin_datastore import create_session
from sqlalchemy import select

from .model import UserBind


async def set_user_srbind(user: UserBind) -> None:
    select_user = await get_user_srbind(user.bot_id, user.user_id)
    async with create_session() as session:
        for old_user in select_user:
            if user.user_id != "0":
                await session.delete(old_user)
            elif user.cookie == old_user.cookie:
                await session.delete(old_user)
        await session.commit()
    async with create_session() as session:
        session.add(user)
        await session.commit()


async def del_user_srbind(bot_id: str, user_id: str, sr_uid: str) -> None:
    select_user = await get_user_srbind(bot_id, user_id)
    select_uid = [user.sr_uid for user in select_user]
    if sr_uid in select_uid:
        user = select_user[select_uid.index(sr_uid)]
        async with create_session() as session:
            await session.delete(user)
            await session.commit()


async def get_user_srbind(bot_id: str, user_id: str) -> List[UserBind]:
    statement = (
        select(UserBind)
        .where(UserBind.bot_id == bot_id)
        .where(UserBind.user_id == user_id)
    )
    async with create_session() as session:
        records = (await session.scalars(statement)).all()
    return list(records)


def generate_qrcode(url: str) -> BytesIO:
    qr = qrcode.QRCode(  # type: ignore
        version=1, error_correction=qrcode.ERROR_CORRECT_L, box_size=10, border=4
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    img.save(bio)
    return bio
