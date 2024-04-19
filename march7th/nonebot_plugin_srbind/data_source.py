from io import BytesIO

import qrcode
from sqlalchemy import select, update
from nonebot_plugin_datastore import create_session

from .model import UserBind


async def set_user_srbind(user: UserBind) -> None:
    select_user = await get_user_srbind(user.bot_id, user.user_id)
    update_flag = False
    for old_user in select_user:
        if user.user_id != "0":
            # not public user
            if user.sr_uid != old_user.sr_uid:
                # delete origin user
                async with create_session() as session:
                    await session.delete(old_user)
                    await session.commit()
            else:
                # update user
                statement = (
                    update(UserBind)
                    .where(UserBind.bot_id == user.bot_id)
                    .where(UserBind.user_id == user.user_id)
                    .where(UserBind.sr_uid == user.sr_uid)
                    .values(mys_id=user.mys_id)
                    .values(device_id=user.device_id)
                    .values(device_fp=user.device_fp)
                    .values(cookie=user.cookie)
                    .values(stoken=user.stoken)
                )
                async with create_session() as session:
                    await session.execute(statement)
                    await session.commit()
                update_flag = True
        else:
            # public user
            if user.cookie == old_user.cookie:
                statement = (
                    update(UserBind)
                    .where(UserBind.bot_id == user.bot_id)
                    .where(UserBind.user_id == user.user_id)
                    .where(UserBind.sr_uid == user.sr_uid)
                    .values(mys_id=user.mys_id)
                    .values(device_id=user.device_id)
                    .values(device_fp=user.device_fp)
                    .values(cookie=user.cookie)
                    .values(stoken=user.stoken)
                )
                async with create_session() as session:
                    await session.execute(statement)
                    await session.commit()
                update_flag = True
    if not update_flag:
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


async def get_user_srbind(bot_id: str, user_id: str) -> list[UserBind]:
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
