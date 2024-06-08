from typing import Optional

from sqlalchemy import TEXT, String
from nonebot_plugin_orm import Model
from sqlalchemy.orm import Mapped, mapped_column


class UserBind(Model):
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(64))
    user_id: Mapped[str] = mapped_column(String(64))
    sr_uid: Mapped[str] = mapped_column(String(64))
    mys_id: Mapped[Optional[str]] = mapped_column(String(64))
    device_id: Mapped[Optional[str]] = mapped_column(String(64))
    device_fp: Mapped[Optional[str]] = mapped_column(String(64))
    cookie: Mapped[Optional[str]] = mapped_column(TEXT)
    stoken: Mapped[Optional[str]] = mapped_column(TEXT)
