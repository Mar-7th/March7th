import random

from nonebot import get_driver, on_command, on_regex, require
from nonebot.params import RegexDict
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_datastore")
require("nonebot_plugin_saa")

from nonebot_plugin_saa import Image, MessageFactory, Text

from .config import plugin_config
from .models import character, light_cone, update_resources

__plugin_meta__ = PluginMetadata(
    name="StarRailWiki",
    description="崩坏：星穹铁道百科",
    usage="""\
查询Wiki:   xxx(角色|光锥)(攻略|材料)
更新资源:   srupdate *superuser
""",
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
    "武器",
    "装备",
]
BASE_TYPE_RE = "(" + "|".join(BASE_TYPE) + ")"
WIKI_TYPE = ["图鉴", "攻略", "材料"]
WIKI_TYPE_RE = "(" + "|".join(WIKI_TYPE) + ")"

WIKI_RE = (
    rf"(?P<name>\w{{0,7}}?)(?P<type>{BASE_TYPE_RE}?{WIKI_TYPE_RE})(?P<res>\w{{0,7}})"
)

wiki_search = on_regex(WIKI_RE, priority=9, block=False)
wiki_renew = on_command(
    "srupdate", aliases={"更新星铁资源列表"}, permission=SUPERUSER, block=True
)


@wiki_search.handle()
async def _(regex_dict: dict = RegexDict()):
    wiki_name: str = regex_dict["name"] or ""
    wiki_type: str = regex_dict.get("type") or ""
    res: str = regex_dict.get("res") or ""
    if wiki_name and res != "":
        await wiki_search.finish()
    if not wiki_name or not wiki_type:
        await wiki_search.finish()
    if "角色" in wiki_type:
        wiki_type_1 = "character"
    elif "光锥" in wiki_type or "武器" in wiki_type or "装备" in wiki_type:
        wiki_type_1 = "light_cone"
    else:
        wiki_type_1 = "all"
    if "材料" in wiki_type:
        wiki_type_2 = "material"
    else:
        wiki_type_2 = "overview"
    pic_content = ""
    if wiki_type_1 in {"all", "character"} and wiki_type_2 == "overview":
        if wiki_name in character:
            character_overview = list(character[wiki_name]["character_overview"])
            pic_content = (
                random.choice(character_overview) if character_overview else ""
            )
    if (
        pic_content == ""
        and wiki_type_1 in {"all", "character"}
        and wiki_type_2 == "material"
    ):
        if wiki_name in character:
            pic_content = character[wiki_name]["character_material"] or ""
    if pic_content == "" and wiki_type_1 in {"all", "light_cone"}:
        if wiki_name in light_cone:
            light_cone_overview = list(light_cone[wiki_name]["light_cone_overview"])
            pic_content = (
                random.choice(light_cone_overview) if light_cone_overview else ""
            )
    if pic_content:
        msg_builder = MessageFactory(
            [
                Image(
                    f"{plugin_config.github_proxy}/{plugin_config.sr_wiki_url}/{pic_content}"
                )
            ]
        )
        await msg_builder.send(at_sender=True)
    await wiki_search.finish()


@wiki_renew.handle()
async def _():
    msg_builder = MessageFactory([Text("开始更新『崩坏：星穹铁道』游戏资源列表")])
    await msg_builder.send()
    await update_resources(overwrite=True)
    msg_builder = MessageFactory([Text("『崩坏：星穹铁道』游戏资源列表更新完成")])
    await msg_builder.send()
    await wiki_renew.finish()
