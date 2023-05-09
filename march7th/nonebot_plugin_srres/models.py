import asyncio
import json
import random
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from nonebot.log import logger
from nonebot_plugin_datastore import get_plugin_data

from .config import plugin_config

plugin_data_dir: Path = get_plugin_data().data_dir


ResFiles = {
    "character": "characters.json",
    "light_cone": "light_cones.json",
    "nickname": "nickname.json",
    "path": "paths.json",
    "element": "elements.json",
}


class StarRailRes:
    character: Dict[str, Any] = {}
    light_cone: Dict[str, Any] = {}
    path: Dict[str, Any] = {}
    element: Dict[str, Any] = {}
    nickname: Dict[str, Any] = {}
    nickname_reverse: Dict[str, Any] = {}

    def proxy_url(self, url: str) -> str:
        if plugin_config.github_proxy:
            return f"{plugin_config.github_proxy}/{url}"
        return url

    def get_icon(
        self, name: Optional[str] = None, id: Optional[str] = None
    ) -> Optional[Path]:
        if name:
            chars = "「」！"
            for char in chars:
                name = name.replace(char, "")
            if name in self.nickname_reverse:
                return self.get_icon(id=self.nickname_reverse[name])
        if id:
            if id in self.character:
                return self.get_icon_character(id)
            if id in self.light_cone:
                return self.get_icon_light_cone(id)
        return None

    def get_icon_character(self, id: str) -> Optional[Path]:
        if id in self.character:
            icon_file = self.character[id].get("icon")
            if icon_file:
                return plugin_data_dir / icon_file
        return None

    def get_icon_light_cone(self, id: str) -> Optional[Path]:
        if id in self.light_cone:
            icon_file = self.light_cone[id].get("icon")
            if icon_file:
                return plugin_data_dir / icon_file
        return None

    def get_icon_path(self, id: str) -> Optional[Path]:
        id = id.capitalize()
        if id in self.path:
            icon_file = self.path[id].get("icon")
            if icon_file:
                return plugin_data_dir / icon_file
        return None

    def get_icon_element(self, id: str) -> Optional[Path]:
        id = id.capitalize()
        if id in self.element:
            icon_file = self.element[id].get("icon")
            if icon_file:
                return plugin_data_dir / icon_file
        return None

    def get_character_preview_url(self, name: str) -> Optional[str]:
        id = self.nickname_reverse[name]
        if id in self.character:
            preview = self.character[name].get("preview")
            if preview:
                return f"{plugin_config.sr_wiki_url}/{preview}"
        return None

    def get_character_portrait_url(self, name: str) -> Optional[str]:
        id = self.nickname_reverse[name]
        if id in self.character:
            portrait = self.character[id].get("portrait")
            if portrait:
                return self.proxy_url(f"{plugin_config.sr_wiki_url}/{portrait}")
        return None

    def get_character_overview_url(self, name: str) -> Optional[str]:
        id = self.nickname_reverse[name]
        if id in self.character:
            overview = self.character[id].get("character_overview")
            if isinstance(overview, list):
                overview = random.choice(overview)
            if overview:
                return self.proxy_url(f"{plugin_config.sr_wiki_url}/{overview}")
        return None

    def get_character_material_url(self, name: str) -> Optional[str]:
        id = self.nickname_reverse[name]
        if id in self.character:
            material = self.character[id].get("character_material")
            if isinstance(material, list):
                material = random.choice(material)
            if material:
                return self.proxy_url(f"{plugin_config.sr_wiki_url}/{material}")
        return None

    def get_light_cone_overview_url(self, name: str) -> Optional[str]:
        id = self.nickname_reverse[name]
        if id in self.light_cone:
            overview = self.light_cone[id].get("light_cone_overview")
            if isinstance(overview, list):
                overview = random.choice(overview)
            if overview:
                return self.proxy_url(f"{plugin_config.sr_wiki_url}/{overview}")
        return None

    def reload(self) -> None:
        with open(
            plugin_data_dir / "index" / ResFiles["character"], "r", encoding="utf-8"
        ) as f:
            self.character = json.load(f)
        with open(
            plugin_data_dir / "index" / ResFiles["light_cone"], "r", encoding="utf-8"
        ) as f:
            self.light_cone = json.load(f)
        with open(
            plugin_data_dir / "index" / ResFiles["nickname"], "r", encoding="utf-8"
        ) as f:
            self.nickname = json.load(f)
        for k, v in dict(self.nickname["characters"]).items():
            for v_item in list(v):
                self.nickname_reverse[v_item] = k
        for k, v in dict(self.nickname["light_cones"]).items():
            for v_item in list(v):
                self.nickname_reverse[v_item] = k
        with open(
            plugin_data_dir / "index" / ResFiles["path"], "r", encoding="utf-8"
        ) as f:
            self.path = json.load(f)
        with open(
            plugin_data_dir / "index" / ResFiles["element"], "r", encoding="utf-8"
        ) as f:
            self.element = json.load(f)

    async def update(self, update_index: bool = False) -> bool:
        async def download(url: str) -> Optional[bytes]:
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

        status: bool = True
        logger.info("正在检查索引文件是否完整")
        if not (plugin_data_dir / "index").exists():
            (plugin_data_dir / "index").mkdir(parents=True)
        for _, file_name in ResFiles.items():
            if not (plugin_data_dir / "index" / file_name).exists() or update_index:
                logger.debug(f"Downloading index {file_name}...")
                data = await download(
                    self.proxy_url(f"{plugin_config.sr_wiki_url}/index/cn/{file_name}")
                )
                if not data:
                    logger.error(f"Failed to download {file_name}.")
                    status = False
                    continue
                with open(plugin_data_dir / "index" / file_name, "wb") as f:
                    f.write(data)
        logger.info("索引文件检查完毕")
        logger.info("正在检查资源文件是否完整")
        character = {}
        light_cone = {}
        path = {}
        element = {}
        all = {}
        with open(
            plugin_data_dir / "index" / ResFiles["character"], "r", encoding="utf-8"
        ) as f:
            character = json.load(f)
        with open(
            plugin_data_dir / "index" / ResFiles["light_cone"], "r", encoding="utf-8"
        ) as f:
            light_cone = json.load(f)
        with open(
            plugin_data_dir / "index" / ResFiles["path"], "r", encoding="utf-8"
        ) as f:
            path = json.load(f)
        with open(
            plugin_data_dir / "index" / ResFiles["element"], "r", encoding="utf-8"
        ) as f:
            element = json.load(f)
        all.update(character)
        all.update(light_cone)
        all.update(path)
        all.update(element)
        for item in all.values():
            icon_file = item["icon"]
            if not (plugin_data_dir / icon_file).exists():
                logger.debug(f"Downloading {icon_file}...")
                data = await download(
                    self.proxy_url(f"{plugin_config.sr_wiki_url}/{icon_file}")
                )
                if not data:
                    logger.error(f"Failed to download {icon_file}.")
                    status = False
                    continue
                (plugin_data_dir / icon_file).parent.mkdir(parents=True, exist_ok=True)
                with open(plugin_data_dir / icon_file, "wb") as f:
                    f.write(data)
                logger.success(f"Succeed to download {icon_file}.")
                await asyncio.sleep(0.1)
        logger.info("资源文件检查完毕")
        self.reload()
        return status
