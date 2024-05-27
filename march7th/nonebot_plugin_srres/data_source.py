import json
import random
import asyncio
from pathlib import Path
from typing import Any, Optional, TypedDict

import httpx
from nonebot.log import logger
from nonebot.compat import type_validate_python
from nonebot_plugin_datastore import get_plugin_data

from .config import plugin_config
from .model.paths import PathIndex
from .model.elements import ElementIndex
from .model.properties import PropertyIndex
from .model.achievements import AchievementIndex
from .model.light_cones import (
    LightConeIndex,
    LightConeRankIndex,
    LightConePromotionIndex,
)
from .model.relics import (
    RelicIndex,
    RelicSetIndex,
    RelicSubAffixIndex,
    RelicMainAffixIndex,
)
from .model.characters import (
    CharacterIndex,
    CharacterRankIndex,
    CharacterSkillIndex,
    CharacterPromotionIndex,
    CharacterSkillTreeIndex,
)

plugin_data_dir: Path = get_plugin_data().data_dir
index_dir = plugin_data_dir / "index"
font_dir = plugin_data_dir / "font"


ResFiles = {
    "characters",
    "character_ranks",
    "character_skills",
    "character_skill_trees",
    "character_promotions",
    "light_cones",
    "light_cone_ranks",
    "light_cone_promotions",
    "relics",
    "relic_sets",
    "relic_main_affixes",
    "relic_sub_affixes",
    "paths",
    "elements",
    "properties",
    "achievements",
    "nickname",
}

NicknameFile = "nickname.json"
VersionFile = "info.json"
FontFile = "SDK_SC_Web.ttf"


class ResIndexType(TypedDict):
    characters: CharacterIndex
    character_ranks: CharacterRankIndex
    character_skills: CharacterSkillIndex
    character_skill_trees: CharacterSkillTreeIndex
    character_promotions: CharacterPromotionIndex
    light_cones: LightConeIndex
    light_cone_ranks: LightConeRankIndex
    light_cone_promotions: LightConePromotionIndex
    relics: RelicIndex
    relic_sets: RelicSetIndex
    relic_main_affixes: RelicMainAffixIndex
    relic_sub_affixes: RelicSubAffixIndex
    paths: PathIndex
    elements: ElementIndex
    properties: PropertyIndex
    achievements: AchievementIndex


class StarRailRes:
    ResIndex: ResIndexType = {
        "characters": {},
        "character_ranks": {},
        "character_skills": {},
        "character_skill_trees": {},
        "character_promotions": {},
        "light_cones": {},
        "light_cone_ranks": {},
        "light_cone_promotions": {},
        "relics": {},
        "relic_sets": {},
        "relic_main_affixes": {},
        "relic_sub_affixes": {},
        "paths": {},
        "elements": {},
        "properties": {},
        "achievements": {},
    }
    Nickname: dict[str, Any] = {}
    NicknameRev: dict[str, Any] = {}

    def proxy_url(self, url: str) -> str:
        if plugin_config.github_proxy:
            github_proxy = plugin_config.github_proxy
            if github_proxy.endswith("/"):
                github_proxy = github_proxy[:-1]
            return f"{github_proxy}/{url}"
        return url

    async def download(self, url: str) -> Optional[bytes]:
        async with httpx.AsyncClient() as client:
            for i in range(3):
                try:
                    resp = await client.get(url, timeout=10)
                    if resp.status_code == 302:
                        url = resp.headers["location"]
                        continue
                    resp.raise_for_status()
                    return resp.content
                except Exception as e:
                    logger.warning(f"Error downloading {url}, retry {i}/3: {e}")
                    await asyncio.sleep(2)
            logger.error(f"Error downloading {url}, all attempts failed.")
            return None

    async def cache(self, file: str, refresh: bool = False):
        status = True
        if not (plugin_data_dir / file).exists() or refresh:
            (plugin_data_dir / file).parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Downloading {file}...")
            data = await self.download(
                self.proxy_url(f"{plugin_config.sr_wiki_url}/{file}")
            )
            if not data:
                logger.error(f"Failed to download {file}.")
                status = False
            else:
                with open(plugin_data_dir / file, "wb") as f:
                    f.write(data)
        return status

    async def get_icon(
        self, name: Optional[str] = None, id: Optional[str] = None
    ) -> Optional[Path]:
        if name:
            chars = "「」！&"
            for char in chars:
                name = name.replace(char, "")
            if name in self.NicknameRev:
                return await self.get_icon(id=self.NicknameRev[name])
        if id:
            if id in self.ResIndex["characters"]:
                return await self.get_icon_character(id)
            if id in self.ResIndex["light_cones"]:
                return await self.get_icon_light_cone(id)
            if id in self.ResIndex["relic_sets"]:
                return await self.get_icon_relic_set(id)
        return None

    async def get_icon_character(self, id: str) -> Optional[Path]:
        if id == "8000":
            id = "8002"
        if id in self.ResIndex["characters"]:
            icon_file = self.ResIndex["characters"][id].icon
            if icon_file:
                if await self.cache(icon_file):
                    return plugin_data_dir / icon_file
        return None

    async def get_icon_light_cone(self, id: str) -> Optional[Path]:
        if id in self.ResIndex["light_cones"]:
            icon_file = self.ResIndex["light_cones"][id].icon
            if icon_file:
                if await self.cache(icon_file):
                    return plugin_data_dir / icon_file
        return None

    async def get_icon_relic_set(self, id: str) -> Optional[Path]:
        if id in self.ResIndex["relic_sets"]:
            icon_file = self.ResIndex["relic_sets"][id].icon
            if icon_file:
                if await self.cache(icon_file):
                    return plugin_data_dir / icon_file
        return None

    async def get_icon_path(self, id: str) -> Optional[Path]:
        id = id.capitalize()
        if id in self.ResIndex["paths"]:
            icon_file = self.ResIndex["paths"][id].icon
            if icon_file:
                if await self.cache(icon_file):
                    return plugin_data_dir / icon_file
        return None

    async def get_icon_element(self, id: str) -> Optional[Path]:
        id = id.capitalize()
        if id in self.ResIndex["elements"]:
            icon_file = self.ResIndex["elements"][id].icon
            if icon_file:
                if await self.cache(icon_file):
                    return plugin_data_dir / icon_file
        return None

    async def get_character_preview(self, name: str) -> Optional[Path]:
        id = self.NicknameRev[name]
        if id == "8000":
            id = "8002"
        if id in self.ResIndex["characters"]:
            preview = self.ResIndex["characters"][name].preview
            if preview:
                if await self.cache(preview):
                    return plugin_data_dir / preview
        return None

    async def get_character_portrait(self, name: str) -> Optional[Path]:
        id = self.NicknameRev[name]
        if id == "8000":
            id = "8002"
        if id in self.ResIndex["characters"]:
            portrait = self.ResIndex["characters"][id].portrait
            if portrait:
                if await self.cache(portrait):
                    return plugin_data_dir / portrait
        return None

    async def get_character_overview(self, name: str) -> Optional[Path]:
        if name not in self.NicknameRev:
            return None
        id = self.NicknameRev[name]
        if id == "8000":
            id = "8002"
        if id in self.ResIndex["characters"]:
            overview = self.ResIndex["characters"][id].guide_overview
            overview = [
                n
                for n in overview
                if any(p in n for p in plugin_config.sr_wiki_providers)
            ]
            if overview:
                if isinstance(overview, list):
                    overview = random.choice(overview)
                if await self.cache(overview):
                    return plugin_data_dir / overview
        return None

    def get_character_overview_url(self, name: str) -> Optional[str]:
        if name not in self.NicknameRev:
            return None
        id = self.NicknameRev[name]
        if id == "8000":
            id = "8002"
        if id in self.ResIndex["characters"]:
            overview = self.ResIndex["characters"][id].guide_overview
            if overview:
                if isinstance(overview, list):
                    overview = random.choice(overview)
                return self.proxy_url(f"{plugin_config.sr_wiki_url}/{overview}")
        return None

    async def get_light_cone_overview(self, name: str) -> Optional[Path]:
        if name not in self.NicknameRev:
            return None
        id = self.NicknameRev[name]
        if id in self.ResIndex["light_cones"]:
            overview = self.ResIndex["light_cones"][id].guide_overview
            overview = [
                n
                for n in overview
                if any(p in n for p in plugin_config.sr_wiki_providers)
            ]
            if overview:
                if isinstance(overview, list):
                    overview = random.choice(overview)
                if await self.cache(overview):
                    return plugin_data_dir / overview
        return None

    def get_light_cone_overview_url(self, name: str) -> Optional[str]:
        if name not in self.NicknameRev:
            return None
        id = self.NicknameRev[name]
        if id in self.ResIndex["light_cones"]:
            overview = self.ResIndex["light_cones"][id].guide_overview
            if overview:
                if isinstance(overview, list):
                    overview = random.choice(overview)
                return self.proxy_url(f"{plugin_config.sr_wiki_url}/{overview}")
        return None

    async def get_relic_set_overview(self, name: str) -> Optional[Path]:
        if name not in self.NicknameRev:
            return None
        id = self.NicknameRev[name]
        if id in self.ResIndex["relic_sets"]:
            overview = self.ResIndex["relic_sets"][id].guide_overview
            if overview:
                if isinstance(overview, list):
                    overview = random.choice(overview)
                if await self.cache(overview):
                    return plugin_data_dir / overview
        return None

    def get_relic_set_overview_url(self, name: str) -> Optional[str]:
        if name not in self.NicknameRev:
            return None
        id = self.NicknameRev[name]
        if id in self.ResIndex["relic_sets"]:
            overview = self.ResIndex["relic_sets"][id].guide_overview
            if overview:
                if isinstance(overview, list):
                    overview = random.choice(overview)
                return self.proxy_url(f"{plugin_config.sr_wiki_url}/{overview}")
        return None

    def get_font(self) -> str:
        return str(plugin_data_dir / "font" / FontFile)

    def get_data_folder(self) -> Path:
        return plugin_data_dir

    def load_index_file(self, name: str, model=True) -> dict[str, Any]:
        if name in ResFiles and (index_dir / f"{name}.json").exists():
            with open(index_dir / f"{name}.json", encoding="utf-8") as f:
                data = json.load(f)
            if not model:
                return data
            return type_validate_python(ResIndexType.__annotations__[name], data)
        return {}

    def reload(self) -> None:
        for name in ResFiles:
            if name in {"nickname"}:
                continue
            self.ResIndex[name] = self.load_index_file(name)
        self.Nickname = self.load_index_file("nickname", model=False)
        for type in {"characters", "light_cones", "relic_sets"}:
            if type in self.Nickname.keys():
                for k, v in dict(self.Nickname[type]).items():
                    for v_item in list(v):
                        self.NicknameRev[v_item] = k

    async def update(self) -> bool:
        """
        更新索引文件
        """
        status: bool = True
        update_index: bool = False
        # 检查是否需要更新
        logger.debug(f"正在下载 {VersionFile}...")
        data = await self.download(
            self.proxy_url(f"{plugin_config.sr_wiki_url}/{VersionFile}")
        )
        if not data:
            logger.error(f"文件 {VersionFile} 下载失败")
            return False
        if not plugin_data_dir.exists() or not (plugin_data_dir / VersionFile).exists():
            plugin_data_dir.mkdir(parents=True, exist_ok=True)
            # 版本文件不存在，更新索引
            update_index = True
        else:
            with open(plugin_data_dir / VersionFile, encoding="utf-8") as f:
                current_version = json.load(f)
            if current_version["timestamp"] != json.loads(data)["timestamp"]:
                # 版本不一致，更新索引
                update_index = True
        # 更新版本文件
        with open(plugin_data_dir / VersionFile, "w", encoding="utf-8") as f:
            f.write(data.decode("utf-8"))
        # 更新索引
        index_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("正在检查索引文件是否完整")
        # 下载索引文件
        for name in ResFiles:
            filename = f"{name}.json"
            if not (index_dir / filename).exists() or update_index:
                # 索引文件不存在或需要更新时下载
                logger.debug(f"正在下载索引 {filename}...")
                data = await self.download(
                    self.proxy_url(
                        f"{plugin_config.sr_wiki_url}/index_min/cn/{filename}"
                    )
                )
                if not data:
                    logger.error(f"文件 {filename} 下载失败")
                    status = False
                    continue
                with open(index_dir / filename, "wb") as f:
                    f.write(data)
        logger.info("索引文件检查完毕")
        if status:
            self.reload()
        # 检查字体文件是否完整
        logger.info("正在检查字体文件是否完整")
        if not font_dir.exists():
            font_dir.mkdir(parents=True)
        filename = FontFile
        if not (font_dir / filename).exists():
            logger.debug(f"正在下载字体文件 {filename}...")
            data = await self.download(
                self.proxy_url(f"{plugin_config.sr_wiki_url}/font/{filename}")
            )
            if not data:
                logger.error(f"文件 {filename} 下载失败")
                status = False
            else:
                with open(font_dir / filename, "wb") as f:
                    f.write(data)
        logger.info("字体文件检查完毕")
        return status

    async def download_guide(self, force: bool = False) -> bool:
        """
        预下载或更新攻略文件

        Args:
            force: 是否强制更新本地文件
        """
        status = True
        guide_files: list[str] = []
        for id in self.ResIndex["characters"]:
            guide_files += self.ResIndex["characters"][id].guide_overview
        for id in self.ResIndex["light_cones"]:
            guide_files += self.ResIndex["light_cones"][id].guide_overview
        for id in self.ResIndex["relic_sets"]:
            guide_files += self.ResIndex["relic_sets"][id].guide_overview
        guide_files = [
            n
            for n in guide_files
            if any(p in n for p in plugin_config.sr_wiki_providers)
        ]
        for file in guide_files:
            if not await self.cache(file, force):
                status = False
        return status
