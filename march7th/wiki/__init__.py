from nonebot import get_driver, on_regex, require
from nonebot.params import RegexDict
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_datastore")
from nonebot_plugin_saa import Image, MessageFactory, Text

from .config import plugin_config
from .model import character, light_cone, mapping_cn, update_resources

__plugin_meta__ = PluginMetadata(
    name="StarRailWiki",
    description="崩坏：星穹铁道百科",
    usage="(角色|武器)(攻略|图鉴|材料)",
    extra={
        "version": "1.0",
    },
)

driver = get_driver()


@driver.on_startup
async def _():
    await update_resources()


BASE_TYPE = [
    "角色",
    "光锥",
]
BASE_TYPE_RE = "(" + "|".join(BASE_TYPE) + ")"
WIKI_TYPE = ["图鉴", "攻略", "材料"]
WIKI_TYPE_RE = "(" + "|".join(WIKI_TYPE) + ")"

WIKI_RE = rf"(?P<name>\w{{0,7}}?)(?P<type>{BASE_TYPE_RE}?{WIKI_TYPE_RE})"

wiki_search = on_regex(WIKI_RE, priority=9, block=True)


@wiki_search.handle()
async def _(regex_dict: dict = RegexDict()):
    wiki_name: str = regex_dict["name"] or ""
    wiki_type: str = regex_dict.get("type") or ""
    if not wiki_name or not wiki_type:
        await wiki_search.finish()
    if "角色" in wiki_type:
        if "材料" in wiki_type:
            wiki_type = "character_material"
        else:
            wiki_type = "character_overview"
    elif "光锥" in wiki_type:
        wiki_type = "light_cone"
    else:
        wiki_type = "all"
    pic_content = ""
    if wiki_type in {"all", "character_overview"}:
        if wiki_name in mapping_cn["character"]:
            wiki_name = mapping_cn[wiki_name]
            character_overview = list(character[wiki_name]["character_overview"])
            pic_content = character_overview[0] if character_overview else ""
    if pic_content == "" and wiki_type in {"all", "character_material"}:
        if wiki_name in mapping_cn["character"]:
            wiki_name = mapping_cn[wiki_name]
            pic_content = character[wiki_name]["character_material"] or ""
    if pic_content == "" and wiki_type in {"all", "light_cone"}:
        if wiki_name in mapping_cn["light_cone"]:
            wiki_name = mapping_cn[wiki_name]
            light_cone_overview = list(light_cone[wiki_name]["light_cone_overview"])
            pic_content = light_cone_overview[0] if light_cone_overview else ""
    if pic_content == "":
        msg_builder = MessageFactory([Text(f"暂无『{regex_dict['name']}』的查找结果")])
    else:
        msg_builder = MessageFactory([Image(pic_content)])
    await msg_builder.send(at_sender=True)
    await wiki_search.finish()
