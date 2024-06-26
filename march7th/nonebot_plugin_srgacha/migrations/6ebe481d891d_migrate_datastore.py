"""migrate datastore

迁移 ID: 6ebe481d891d
父迁移: bee999fdc54c
创建时间: 2024-06-08 17:51:10.690206

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from alembic.op import run_async
from sqlalchemy.orm import Session
from nonebot import logger, require
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import Connection, select, inspect
from sqlalchemy.ext.asyncio import AsyncConnection

revision: str = "6ebe481d891d"
down_revision: str | Sequence[str] | None = "bee999fdc54c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _migrate_old_data(ds_conn: Connection):
    insp = inspect(ds_conn)
    if (
        "nonebot_plugin_srgacha_usergachalog" not in insp.get_table_names()
        or "nonebot_plugin_srgacha_alembic_version" not in insp.get_table_names()
    ):
        logger.debug("No datastore database of plugin nonebot_plugin_srgacha")
        return

    DsBase = automap_base()
    DsBase.prepare(autoload_with=ds_conn)
    DsUserGachaLog = DsBase.classes.nonebot_plugin_srgacha_usergachalog

    Base = automap_base()
    Base.prepare(autoload_with=op.get_bind())
    UserGachaLog = Base.classes.nonebot_plugin_srgacha_usergachalog

    ds_session = Session(ds_conn)
    session = Session(op.get_bind())

    count = ds_session.query(DsUserGachaLog).count()
    if count == 0:
        logger.info("No datastore data of plugin nonebot_plugin_srgacha")
        return

    AlembicVersion = DsBase.classes.nonebot_plugin_srgacha_alembic_version
    version_num = ds_session.scalars(select(AlembicVersion.version_num)).one_or_none()
    if not version_num:
        return
    if version_num != "14fdb105081e":
        logger.warning(
            "Old database is not latest version, "
            "please use `nb datastore upgrade` in v0.2.0 first"
        )
        raise RuntimeError(
            "You should upgrade old database in v0.2.0 first to migrate data"
        )

    logger.info("Migrating nonebot_plugin_srgacha data from datastore")
    user_gachalog_list = ds_session.query(DsUserGachaLog).all()
    for user_gachalog in user_gachalog_list:
        session.add(
            UserGachaLog(
                id=user_gachalog.id,
                bot_id=user_gachalog.bot_id,
                user_id=user_gachalog.user_id,
                sr_uid=user_gachalog.sr_uid,
                gacha=user_gachalog.gacha,
            )
        )
    session.commit()
    logger.success("Migrate nonebot_plugin_srgacha data from datastore successfully")


async def data_migrate(conn: AsyncConnection):
    from nonebot_plugin_datastore.db import get_engine

    async with get_engine().connect() as ds_conn:
        await ds_conn.run_sync(_migrate_old_data)


def upgrade(name: str = "") -> None:
    if name:
        return
    # ### commands auto generated by Alembic - please adjust! ###
    try:
        require("nonebot_plugin_datastore")
    except RuntimeError:
        return

    run_async(data_migrate)
    # ### end Alembic commands ###


def downgrade(name: str = "") -> None:
    if name:
        return
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
