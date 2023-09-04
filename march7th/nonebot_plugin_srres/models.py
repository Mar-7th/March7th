import asyncio
import json
import random
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx
from nonebot.log import logger
from nonebot_plugin_datastore import get_plugin_data

from .config import plugin_config

plugin_data_dir: Path = get_plugin_data().data_dir
index_dir = plugin_data_dir / "index"
font_dir = plugin_data_dir / "font"


ResFiles = {
    "characters": "characters.json",
    "character_ranks": "character_ranks.json",
    "character_skills": "character_skills.json",
    "character_skill_trees": "character_skill_trees.json",
    "character_promotions": "character_promotions.json",
    "light_cones": "light_cones.json",
    "light_cone_ranks": "light_cone_ranks.json",
    "light_cone_promotions": "light_cone_promotions.json",
    "relics": "relics.json",
    "relic_sets": "relic_sets.json",
    "relic_main_affixes": "relic_main_affixes.json",
    "relic_sub_affixes": "relic_sub_affixes.json",
    "paths": "paths.json",
    "elements": "elements.json",
    "properties": "properties.json",
}

NicknameFile = "nickname.json"
FontFile = "SDK_SC_Web.ttf"


class StarRailRes:
    ResIndex: Dict[str, Dict[str, Any]] = {}
    Nickname: Dict[str, Any] = {}
    NicknameRev: Dict[str, Any] = {}

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

    async def cache(self, file: str):
        status = True
        if not (plugin_data_dir / file).exists():
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
            chars = "「」！"
            for char in chars:
                name = name.replace(char, "")
            if name in self.NicknameRev:
                return await self.get_icon(id=self.NicknameRev[name])
        if id:
            if id in self.ResIndex["characters"]:
                return await self.get_icon_character(id)
            if id in self.ResIndex["light_cones"]:
                return await self.get_icon_light_cone(id)
            if id in self.ResIndex["relic_set"]:
                return await self.get_icon_relic_set(id)
        return None

    async def get_icon_character(self, id: str) -> Optional[Path]:
        if id == "8000":
            id = "8002"
        if id in self.ResIndex["characters"]:
            icon_file = self.ResIndex["characters"][id].get("icon")
            if icon_file:
                if await self.cache(icon_file):
                    return plugin_data_dir / icon_file
        return None

    async def get_icon_light_cone(self, id: str) -> Optional[Path]:
        if id in self.ResIndex["light_cones"]:
            icon_file = self.ResIndex["light_cones"][id].get("icon")
            if icon_file:
                if await self.cache(icon_file):
                    return plugin_data_dir / icon_file
        return None

    async def get_icon_relic_set(self, id: str) -> Optional[Path]:
        if id in self.ResIndex["relic_sets"]:
            icon_file = self.ResIndex["relic_sets"][id].get("icon")
            if icon_file:
                if await self.cache(icon_file):
                    return plugin_data_dir / icon_file
        return None

    async def get_icon_path(self, id: str) -> Optional[Path]:
        id = id.capitalize()
        if id in self.ResIndex["paths"]:
            icon_file = self.ResIndex["paths"][id].get("icon")
            if icon_file:
                if await self.cache(icon_file):
                    return plugin_data_dir / icon_file
        return None

    async def get_icon_element(self, id: str) -> Optional[Path]:
        id = id.capitalize()
        if id in self.ResIndex["elements"]:
            icon_file = self.ResIndex["elements"][id].get("icon")
            if icon_file:
                if await self.cache(icon_file):
                    return plugin_data_dir / icon_file
        return None

    async def get_character_preview(self, name: str) -> Optional[str]:
        id = self.NicknameRev[name]
        if id == "8000":
            id = "8002"
        if id in self.ResIndex["characters"]:
            preview = self.ResIndex["characters"][name].get("preview")
            if preview:
                if await self.cache(preview):
                    return plugin_data_dir / preview
        return None

    async def get_character_portrait(self, name: str) -> Optional[str]:
        id = self.NicknameRev[name]
        if id == "8000":
            id = "8002"
        if id in self.ResIndex["characters"]:
            portrait = self.ResIndex["characters"][id].get("portrait")
            if portrait:
                if await self.cache(portrait):
                    return plugin_data_dir / portrait
        return None

    async def get_character_overview(self, name: str) -> Optional[str]:
        if name not in self.NicknameRev:
            return None
        id = self.NicknameRev[name]
        if id == "8000":
            id = "8002"
        if id in self.ResIndex["characters"]:
            overview = self.ResIndex["characters"][id].get("guide_overview")
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
            overview = self.ResIndex["characters"][id].get("guide_overview")
            if overview:
                if isinstance(overview, list):
                    overview = random.choice(overview)
                return self.proxy_url(f"{plugin_config.sr_wiki_url}/{overview}")
        return None

    async def get_character_material(self, name: str) -> Optional[str]:
        if name not in self.NicknameRev:
            return None
        id = self.NicknameRev[name]
        if id == "8000":
            id = "8002"
        if id in self.ResIndex["characters"]:
            material = self.ResIndex["characters"][id].get("guide_material")
            if material:
                if isinstance(material, list):
                    material = random.choice(material)
                if await self.cache(material):
                    return plugin_data_dir / material
        return None

    def get_character_material_url(self, name: str) -> Optional[str]:
        if name not in self.NicknameRev:
            return None
        id = self.NicknameRev[name]
        if id == "8000":
            id = "8002"
        if id in self.ResIndex["characters"]:
            material = self.ResIndex["characters"][id].get("guide_material")
            if material:
                if isinstance(material, list):
                    material = random.choice(material)
                return self.proxy_url(f"{plugin_config.sr_wiki_url}/{material}")
        return None

    def get_character_evaluation_url_and_link(
        self, name: str
    ) -> Optional[Tuple[str, str]]:
        if name not in self.NicknameRev:
            return None
        id = self.NicknameRev[name]
        if id == "8000":
            id = "8002"
        if id in self.ResIndex["characters"]:
            evaluation = self.ResIndex["characters"][id].get("guide_evaluation")
            if evaluation:
                if isinstance(evaluation, list):
                    evaluation = random.choice(evaluation)
                if "image" not in evaluation or "link" not in evaluation:
                    return None
                url = f"{plugin_config.sr_wiki_url}/{evaluation['image']}"
                link = str(evaluation["link"])
                return self.proxy_url(url), link
        return None

    async def get_light_cone_overview(self, name: str) -> Optional[str]:
        if name not in self.NicknameRev:
            return None
        id = self.NicknameRev[name]
        if id in self.ResIndex["light_cones"]:
            overview = self.ResIndex["light_cones"][id].get("guide_overview")
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
            overview = self.ResIndex["light_cones"][id].get("guide_overview")
            if overview:
                if isinstance(overview, list):
                    overview = random.choice(overview)
                return self.proxy_url(f"{plugin_config.sr_wiki_url}/{overview}")
        return None

    async def get_relic_set_overview(self, name: str) -> Optional[str]:
        if name not in self.NicknameRev:
            return None
        id = self.NicknameRev[name]
        if id in self.ResIndex["relic_sets"]:
            overview = self.ResIndex["relic_sets"][id].get("guide_overview")
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
            overview = self.ResIndex["relic_sets"][id].get("guide_overview")
            if overview:
                if isinstance(overview, list):
                    overview = random.choice(overview)
                return self.proxy_url(f"{plugin_config.sr_wiki_url}/{overview}")
        return None

    def get_font(self) -> str:
        return str(plugin_data_dir / "font" / FontFile)

    def get_data_folder(self) -> Path:
        return plugin_data_dir

    def reload(self) -> None:
        for k in ResFiles.keys():
            self.ResIndex[k] = {}
            with open(index_dir / ResFiles[k], "r", encoding="utf-8") as f:
                self.ResIndex[k] = json.load(f)
        with open(index_dir / NicknameFile, "r", encoding="utf-8") as f:
            self.Nickname = json.load(f)
        for type in {"characters", "light_cones", "relic_sets"}:
            if type in self.Nickname.keys():
                for k, v in dict(self.Nickname[type]).items():
                    for v_item in list(v):
                        self.NicknameRev[v_item] = k

    async def update(self, update_index: bool = False) -> bool:
        status: bool = True
        # index
        logger.info("正在检查索引文件是否完整")
        if not index_dir.exists():
            index_dir.mkdir(parents=True)
        # index files
        for _, file_name in ResFiles.items():
            if not (index_dir / file_name).exists() or update_index:
                logger.debug(f"Downloading index {file_name}...")
                data = await self.download(
                    self.proxy_url(
                        f"{plugin_config.sr_wiki_url}/index_min/cn/{file_name}"
                    )
                )
                if not data:
                    logger.error(f"Failed to download {file_name}.")
                    status = False
                    continue
                with open(index_dir / file_name, "wb") as f:
                    f.write(data)
        # nickname
        file_name = NicknameFile
        if not (index_dir / file_name).exists() or update_index:
            logger.debug(f"Downloading index {file_name}...")
            data = await self.download(
                self.proxy_url(f"{plugin_config.sr_wiki_url}/index_min/cn/{file_name}")
            )
            if not data:
                logger.error(f"Failed to download {file_name}.")
                status = False
            else:
                with open(index_dir / file_name, "wb") as f:
                    f.write(data)
        logger.info("索引文件检查完毕")
        if status:
            self.reload()
        # font
        logger.info("正在检查字体文件是否完整")
        if not font_dir.exists():
            font_dir.mkdir(parents=True)
        file_name = FontFile
        if not (font_dir / file_name).exists():
            logger.debug(f"Downloading index {file_name}...")
            data = await self.download(
                self.proxy_url(f"{plugin_config.sr_wiki_url}/font/{file_name}")
            )
            if not data:
                logger.error(f"Failed to download {file_name}.")
                status = False
            else:
                with open(font_dir / file_name, "wb") as f:
                    f.write(data)
        logger.info("字体文件检查完毕")
        return status
