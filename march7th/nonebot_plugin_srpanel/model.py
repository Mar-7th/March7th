import json
from datetime import datetime
from typing import Any, Optional

from nonebot import get_driver
from nonebot.log import logger
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Mapped, mapped_column
from nonebot_plugin_orm import Model, get_session
from nonebot_plugin_localstore import get_data_dir
from sqlalchemy import JSON, String, select, update
from nonebot.drivers import Request, HTTPClientMixin
from nonebot.compat import model_dump, type_validate_python

from .config import plugin_config

score_file = get_data_dir("nonebot_plugin_srpanel") / "score.json"


driver = get_driver()
if not isinstance(driver, HTTPClientMixin):
    raise RuntimeError(
        f"当前驱动配置 {driver} 无法进行 HTTP 请求，请在 DRIVER 配置项末尾添加 +~httpx"
    )


class LevelInfo(BaseModel):
    id: str
    level: int = 0


class AvatarInfo(BaseModel):
    id: str
    name: str
    icon: str


class PathInfo(BaseModel):
    id: str
    name: str
    icon: str


class ElementInfo(BaseModel):
    id: str
    name: str
    color: str
    icon: str


class SkillInfo(BaseModel):
    id: str
    name: str
    level: int
    max_level: int
    element: Optional[ElementInfo]
    type: str
    type_text: str
    effect: str
    effect_text: str
    simple_desc: str
    desc: str
    icon: str


class SkillTreeInfo(BaseModel):
    id: str
    level: int
    max_level: int
    anchor: str
    icon: str
    parent: Optional[str] = None


class PropertyInfo(BaseModel):
    type: str
    field: str
    name: str
    icon: str
    value: float
    display: str
    percent: bool


class AttributeInfo(BaseModel):
    field: str
    name: str
    icon: str
    value: float
    display: str
    percent: bool


class SubAffixInfo(PropertyInfo):
    count: int
    step: int


class RelicInfo(BaseModel):
    id: str
    name: str
    set_id: str
    set_name: str
    rarity: int
    level: int
    icon: str
    main_affix: Optional[PropertyInfo] = None
    sub_affix: list[SubAffixInfo] = []


class RelicSetInfo(BaseModel):
    id: str
    name: str
    num: int
    icon: str
    desc: str = ""
    properties: list[PropertyInfo] = []


class LightConeInfo(BaseModel):
    id: str
    name: str
    rarity: int
    rank: int
    level: int
    promotion: int
    icon: str
    preview: str
    portrait: str
    path: Optional[PathInfo] = None
    attributes: list[AttributeInfo] = []
    properties: list[PropertyInfo] = []


class MemoryInfo(BaseModel):
    level: int = 0
    chaos_id: Optional[int] = None
    chaos_level: Optional[int] = None


class SpaceInfo(BaseModel):
    memory_data: Optional[MemoryInfo] = None
    universe_level: int = 0
    light_cone_count: int = 0
    avatar_count: int = 0
    achievement_count: int = 0


class PlayerInfo(BaseModel):
    uid: str
    nickname: str
    level: int = 0
    world_level: int = 0
    friend_count: int = 0
    avatar: Optional[AvatarInfo] = None
    signature: str = ""
    is_display: bool = False
    space_info: Optional[SpaceInfo] = None


class CharacterInfo(BaseModel):
    id: str
    name: str
    rarity: int
    rank: int
    level: int
    promotion: int
    icon: str
    preview: str
    portrait: str
    rank_icons: list[str] = []
    path: Optional[PathInfo] = None
    element: Optional[ElementInfo] = None
    skills: list[SkillInfo] = []
    skill_trees: list[SkillTreeInfo] = []
    light_cone: Optional[LightConeInfo] = None
    relics: list[RelicInfo] = []
    relic_sets: list[RelicSetInfo] = []
    attributes: list[AttributeInfo] = []
    additions: list[AttributeInfo] = []
    properties: list[PropertyInfo] = []
    # extra
    time: Optional[str] = None


class FormattedApiInfo(BaseModel):
    player: PlayerInfo
    characters: list[CharacterInfo] = []


class ScoreItem(BaseModel):
    weight: dict[str, float]
    main: dict[str, dict[str, float]]
    max: float


ScoreFile = dict[str, ScoreItem]


class UserPanel(Model):
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(64))
    user_id: Mapped[str] = mapped_column(String(64))
    sr_uid: Mapped[str] = mapped_column(String(64))
    cid: Mapped[str] = mapped_column(String(64))
    info: Mapped[dict[str, Any]] = mapped_column(JSON)


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
        async with get_session() as session:
            await session.execute(statement)
            await session.commit()
    else:
        async with get_session() as session:
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
    async with get_session() as session:
        records = (await session.scalars(statement)).all()
    if records:
        return records[0]
    return None


async def get_srpanel_player(
    bot_id: str, user_id: str, sr_uid: str
) -> Optional[PlayerInfo]:
    panel = await get_user_srpanel(bot_id, user_id, sr_uid, "0")
    if panel:
        try:
            return type_validate_python(PlayerInfo, panel.info)
        except Exception:
            return None
    return None


async def get_srpanel_character(
    bot_id: str, user_id: str, sr_uid: str, cid: str
) -> Optional[CharacterInfo]:
    panel = await get_user_srpanel(bot_id, user_id, sr_uid, cid)
    if panel:
        try:
            return type_validate_python(CharacterInfo, panel.info)
        except Exception:
            return None
    return None


async def request(url: str) -> Optional[dict]:
    request = Request(
        "GET",
        url,
        headers={"User-Agent": "Mar-7th/March7th"},
        timeout=10,
    )
    response = await driver.request(request)  # type: ignore
    try:
        data = json.loads(response.content or "{}")
        return data
    except (json.JSONDecodeError, KeyError):
        return None


async def update_score_file() -> Optional[ScoreFile]:
    url = plugin_config.sr_score_url
    if not url:
        logger.error("Cannot get config: sr_score_url")
        return None
    if (
        url.startswith("https://raw.githubusercontent.com")
        and plugin_config.github_proxy
    ):
        url = plugin_config.github_proxy + "/" + url
    sr_score_data = await request(url)
    if not sr_score_data:
        if not score_file.exists():
            return None
        logger.warning("Cannot get local score.json")
        with open(score_file, encoding="utf-8") as f:
            sr_score_data = json.load(f)
    score = {k: type_validate_python(ScoreItem, v) for k, v in sr_score_data.items()}
    with open(score_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(sr_score_data))
    return score


async def update_srpanel(bot_id: str, user_id: str, sr_uid: str) -> Optional[str]:
    url = f"{plugin_config.sr_panel_url}{sr_uid}"
    data = await request(url)
    if not data:
        return None
    try:
        parsed_data = type_validate_python(FormattedApiInfo, data)
    except (ValidationError, KeyError) as e:
        logger.info(f"Can not parse: {data}, error: {e}")
        return None
    player = parsed_data.player
    panel = UserPanel(
        bot_id=bot_id,
        user_id=user_id,
        sr_uid=sr_uid,
        cid="0",
        info=model_dump(player),
    )
    await set_user_srpanel(panel)
    characters = parsed_data.characters
    name_set = set()
    for character in characters:
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        character.time = time
        name_set.add(character.name)
        cid = character.id
        if cid.startswith("80"):
            cid = "8000"
        character_panel = UserPanel(
            bot_id=bot_id,
            user_id=user_id,
            sr_uid=sr_uid,
            cid=cid,
            info=character.dict(),
        )
        await set_user_srpanel(character_panel)
    ret_msg = ""
    for name in name_set:
        name = name.replace("{NICKNAME}", player.nickname)
        ret_msg += f"{name} "
    return ret_msg.strip()
