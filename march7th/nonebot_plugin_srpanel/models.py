import json
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from nonebot_plugin_datastore import create_session, get_plugin_data
from sqlalchemy import JSON, String, select, update
from sqlalchemy.orm import Mapped, mapped_column

from .api import parse
from .config import plugin_config

plugin_data = get_plugin_data()
Model = plugin_data.Model


class UserPanel(Model):
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(64))
    user_id: Mapped[str] = mapped_column(String(64))
    sr_uid: Mapped[str] = mapped_column(String(64))
    cid: Mapped[str] = mapped_column(String(64))
    info: Mapped[Dict[str, Any]] = mapped_column(JSON)


async def set_user_srpanel(panel: UserPanel) -> None:
    select_panel = await get_user_srpanel(
        panel.bot_id, panel.user_id, panel.sr_uid, panel.cid
    )
    if select_panel:
        statement = (
            update(UserPanel)
            .where(UserPanel.id == select_panel.id)
            .values(info=panel.info)
        )
        async with create_session() as session:
            await session.execute(statement)
            await session.commit()
    else:
        async with create_session() as session:
            session.add(panel)
            await session.commit()


async def get_user_srpanel(
    bot_id: str, user_id: str, sr_uid: str, cid: str
) -> Optional[UserPanel]:
    statement = select(UserPanel).where(
        UserPanel.bot_id == bot_id,
        UserPanel.user_id == user_id,
        UserPanel.sr_uid == sr_uid,
        UserPanel.cid == cid,
    )
    async with create_session() as session:
        records = (await session.scalars(statement)).all()
    if records:
        return records[0]
    return None


async def get_srpanel_info(
    bot_id: str, user_id: str, sr_uid: str, cid: str
) -> Optional[Dict[str, Any]]:
    panel = await get_user_srpanel(bot_id, user_id, sr_uid, cid)
    if panel:
        return panel.info
    return None


async def request(url: str):
    async with httpx.AsyncClient(headers={"User-Agent": "Mar-7th/March7th"}) as client:
        data = await client.get(
            url=url,
            timeout=10,
        )
        try:
            data = data.json()
            return data
        except (json.JSONDecodeError, KeyError):
            return None


async def update_srpanel(bot_id: str, user_id: str, sr_uid: str) -> Optional[str]:
    url = f"{plugin_config.sr_panel_url}{sr_uid}"
    data = await request(url)
    if not data:
        return None
    try:
        parsed_data = await parse(data)
    except KeyError:
        return None
    player = parsed_data["player"]
    panel = UserPanel(
        bot_id=bot_id,
        user_id=user_id,
        sr_uid=sr_uid,
        cid="0",
        info=player,
    )
    await set_user_srpanel(panel)
    characters = parsed_data["characters"]
    name_set = set()
    for character in characters:
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        character["time"] = time
        name_set.add(character["name"])
        cid = character["id"]
        if str(cid).startswith("80"):
            cid = "8000"
        character_panel = UserPanel(
            bot_id=bot_id,
            user_id=user_id,
            sr_uid=sr_uid,
            cid=cid,
            info=character,
        )
        await set_user_srpanel(character_panel)
    ret_msg = ""
    for name in name_set:
        name = name.replace("{NICKNAME}", player["name"])
        ret_msg += f"{name} "
    return ret_msg.strip()
