from typing import Any, Dict, List

from sqlalchemy import JSON, String
from pydantic import Field, BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from nonebot_plugin_datastore import get_plugin_data

plugin_data = get_plugin_data()
Model = plugin_data.Model


class GachaLogItem(BaseModel):
    id: str
    gacha_id: str
    gacha_type: str
    item_type: str
    item_id: str
    rank_type: str
    name: str
    count: str
    time: str


class GachaLogData(BaseModel):
    size: str
    list: List[GachaLogItem] = Field(default_factory=list)


class GachaLogResponse(BaseModel):
    retcode: int
    message: str
    data: GachaLogData


class GachaLog(BaseModel):
    common: Dict[str, GachaLogItem] = {}
    """
    Stellar Warp
    """
    beginner: Dict[str, GachaLogItem] = {}
    """
    Departure Warp
    """
    character_event: Dict[str, GachaLogItem] = {}
    """
    Character Event Warp
    """
    light_cone_event: Dict[str, GachaLogItem] = {}
    """
    Light Cone Event Warp
    """


class UserGachaLog(Model):
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(64))
    user_id: Mapped[str] = mapped_column(String(64))
    sr_uid: Mapped[str] = mapped_column(String(64))
    gacha: Mapped[Dict[str, Any]] = mapped_column(JSON)
    """
    JSON of GachaLog
    """
