import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from nonebot.log import logger
from nonebot_plugin_datastore import get_plugin_data

from .config import (
    CHARACTER_FILE_NAME,
    LIGHT_CONE_FILE_NAME,
    plugin_config,
)

plugin_data_dir: Path = get_plugin_data().data_dir

character: Dict[str, Any] = {}
light_cone: Dict[str, Any] = {}


async def update_resources(overwrite: bool = False):
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

    logger.info("Checking wiki resources...")
    for FILE in [LIGHT_CONE_FILE_NAME, CHARACTER_FILE_NAME]:
        if not (plugin_data_dir / FILE).exists() or overwrite:
            logger.info(f"Downloading {FILE}...")
            data = await download(
                f"{plugin_config.github_proxy}/{plugin_config.sr_wiki_url}/{FILE}"
            )
            if not data:
                logger.error(f"Failed to download {FILE}.")
                continue
            with open(plugin_data_dir / FILE, "wb") as f:
                f.write(data)
    logger.info("Wiki resources checked.")
    with open(plugin_data_dir / CHARACTER_FILE_NAME, "r", encoding="utf-8") as f:
        character.update(eval(f.read()))
    with open(plugin_data_dir / LIGHT_CONE_FILE_NAME, "r", encoding="utf-8") as f:
        light_cone.update(eval(f.read()))
