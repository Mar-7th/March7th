import asyncio
import json
import random
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from nonebot.log import logger
from nonebot_plugin_datastore import get_plugin_data

from .config import plugin_config

plugin_data_dir: Path = get_plugin_data().data_dir


class ResFile(Enum):
    CHARACTER = "character_cn.json"
    LIGHT_CONE = "light_cone_cn.json"
    NICKNAME = "nickname_cn.json"
    PATH = "path.json"
    ELEMENT = "element.json"


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

    def icon(self, name: str, use_nickname: bool = False) -> Optional[Path]:
        chars = "「」！"
        for char in chars:
            name = name.replace(char, "")
        if name in self.character:
            return self.icon_character(name)
        if name in self.light_cone:
            return self.icon_light_cone(name)
        if use_nickname and name in self.nickname_reverse:
            return self.icon(self.nickname_reverse[name])
        return None

    def icon_character(self, name: str) -> Optional[Path]:
        if name in self.character:
            icon_file = self.character[name].get("icon")
            if icon_file:
                return plugin_data_dir / icon_file
        return None

    def icon_light_cone(self, name: str) -> Optional[Path]:
        chars = "「」！"
        for char in chars:
            name = name.replace(char, "")
        if name in self.light_cone:
            icon_file = self.light_cone[name].get("icon")
            if icon_file:
                return plugin_data_dir / icon_file
        return None

    def icon_path(self, name: str) -> Optional[Path]:
        name = name.capitalize()
        if name in self.path:
            icon_file = self.path[name].get("icon")
            if icon_file:
                return plugin_data_dir / icon_file
        return None

    def icon_element(self, name: str) -> Optional[Path]:
        name = name.capitalize()
        if name in self.element:
            icon_file = self.element[name].get("icon")
            if icon_file:
                return plugin_data_dir / icon_file
        return None

    def character_preview_url(
        self, name: str, use_nickname: bool = False
    ) -> Optional[str]:
        if name in self.character:
            preview = self.character[name].get("preview")
            if preview:
                return f"{plugin_config.sr_wiki_url}/{preview}"
        if use_nickname and name in self.nickname_reverse:
            return self.character_preview_url(self.nickname_reverse[name])
        return None

    def character_portrait_url(
        self, name: str, use_nickname: bool = False
    ) -> Optional[str]:
        if name in self.character:
            portrait = self.character[name].get("portrait")
            if portrait:
                return self.proxy_url(f"{plugin_config.sr_wiki_url}/{portrait}")
        if use_nickname and name in self.nickname_reverse:
            return self.character_portrait_url(self.nickname_reverse[name])
        return None

    def character_overview_url(
        self, name: str, use_nickname: bool = False
    ) -> Optional[str]:
        if name in self.character:
            overview = self.character[name].get("character_overview")
            if isinstance(overview, list):
                overview = random.choice(overview)
            if overview:
                return self.proxy_url(f"{plugin_config.sr_wiki_url}/{overview}")
        if use_nickname and name in self.nickname_reverse:
            return self.character_overview_url(self.nickname_reverse[name])
        return None

    def character_material_url(
        self, name: str, use_nickname: bool = False
    ) -> Optional[str]:
        if name in self.character:
            material = self.character[name].get("character_material")
            if isinstance(material, list):
                material = random.choice(material)
            if material:
                return self.proxy_url(f"{plugin_config.sr_wiki_url}/{material}")
        if use_nickname and name in self.nickname_reverse:
            return self.character_material_url(self.nickname_reverse[name])
        return None

    def light_cone_overview_url(
        self, name: str, use_nickname: bool = False
    ) -> Optional[str]:
        if name in self.light_cone:
            overview = self.light_cone[name].get("light_cone_overview")
            if isinstance(overview, list):
                overview = random.choice(overview)
            if overview:
                return self.proxy_url(f"{plugin_config.sr_wiki_url}/{overview}")
        if use_nickname and name in self.nickname_reverse:
            return self.light_cone_overview_url(self.nickname_reverse[name])
        return None

    def reload(self) -> None:
        with open(
            plugin_data_dir / ResFile.CHARACTER.value, "r", encoding="utf-8"
        ) as f:
            self.character = json.load(f)
        with open(
            plugin_data_dir / ResFile.LIGHT_CONE.value, "r", encoding="utf-8"
        ) as f:
            self.light_cone = json.load(f)
        with open(plugin_data_dir / ResFile.NICKNAME.value, "r", encoding="utf-8") as f:
            self.nickname = json.load(f)
        for k, v in dict(self.nickname["character"]).items():
            for v_item in list(v):
                self.nickname_reverse[v_item] = k
        for k, v in dict(self.nickname["light_cone"]).items():
            for v_item in list(v):
                self.nickname_reverse[v_item] = k
        with open(plugin_data_dir / ResFile.PATH.value, "r", encoding="utf-8") as f:
            self.path = json.load(f)
        with open(plugin_data_dir / ResFile.ELEMENT.value, "r", encoding="utf-8") as f:
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
        for file in ResFile:
            file_name = file.value
            if not (plugin_data_dir / file_name).exists() or update_index:
                logger.debug(f"Downloading {file_name}...")
                data = await download(
                    self.proxy_url(f"{plugin_config.sr_wiki_url}/{file_name}")
                )
                if not data:
                    logger.error(f"Failed to download {file_name}.")
                    status = False
                    continue
                with open(plugin_data_dir / file_name, "wb") as f:
                    f.write(data)
        logger.info("索引文件检查完毕")
        logger.info("正在检查资源文件是否完整")
        character = {}
        light_cone = {}
        path = {}
        element = {}
        all = {}
        with open(
            plugin_data_dir / ResFile.CHARACTER.value, "r", encoding="utf-8"
        ) as f:
            character = json.load(f)
        with open(
            plugin_data_dir / ResFile.LIGHT_CONE.value, "r", encoding="utf-8"
        ) as f:
            light_cone = json.load(f)
        with open(plugin_data_dir / ResFile.PATH.value, "r", encoding="utf-8") as f:
            path = json.load(f)
        with open(plugin_data_dir / ResFile.ELEMENT.value, "r", encoding="utf-8") as f:
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
                await asyncio.sleep(0.1)
        logger.info("资源文件检查完毕")
        self.reload()
        return status
