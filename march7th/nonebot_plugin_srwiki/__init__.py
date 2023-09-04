import random

from nonebot import on_regex, require
from nonebot.params import RegexDict
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_saa")
require("nonebot_plugin_srres")

from nonebot_plugin_saa import Image, MessageFactory, Text

try:
    from march7th.nonebot_plugin_srres import srres
except ModuleNotFoundError:
    from nonebot_plugin_srres import srres

__plugin_meta__ = PluginMetadata(
    name="StarRailWiki",
    description="崩坏：星穹铁道百科",
    usage="""\
查询Wiki:   xxx(角色|光锥|遗器)(攻略|材料|测评)
""",
    extra={
        "version": "1.0",
        "srhelp": """\
查询Wiki: [u]xxx[/u]角色攻略
支持 角色攻略/材料 光锥/遗器图鉴
""",
    },
)

BASE_TYPE = [
    "角色",
    "光锥",
    "武器",
    "装备",
    "遗器",
]
BASE_TYPE_RE = "(" + "|".join(BASE_TYPE) + ")"
WIKI_TYPE = ["图鉴", "攻略", "材料", "测评", "评测"]
WIKI_TYPE_RE = "(" + "|".join(WIKI_TYPE) + ")"

WIKI_RE = (
    rf"(?P<name>\w{{0,10}}?)(?P<type>{BASE_TYPE_RE}?{WIKI_TYPE_RE})(?P<res>\w{{0,10}})"
)

wiki_search = on_regex(WIKI_RE, priority=9, block=False)


@wiki_search.handle()
async def _(regex_dict: dict = RegexDict()):
    wiki_name: str = regex_dict["name"] or ""
    wiki_type: str = regex_dict.get("type") or ""
    res: str = regex_dict.get("res") or ""
    if wiki_name and res:
        await wiki_search.finish()
    if not wiki_name or not wiki_type:
        await wiki_search.finish()
    if not wiki_name and res:
        wiki_name = res
    if "角色" in wiki_type:
        wiki_type_1 = "character"
    elif "光锥" in wiki_type or "武器" in wiki_type or "装备" in wiki_type:
        wiki_type_1 = "light_cone"
    elif "遗器" in wiki_type:
        wiki_type_1 = "relic_set"
    else:
        wiki_type_1 = "all"
    if "材料" in wiki_type:
        wiki_type_2 = "material"
    else:
        wiki_type_2 = "overview"
    pic_content = None
    if wiki_type_1 in {"all", "character"} and wiki_type_2 == "overview":
        pic_content = await srres.get_character_overview(wiki_name)
    if (
        not pic_content
        and wiki_type_1 in {"all", "character"}
        and wiki_type_2 == "material"
    ):
        pic_content = await srres.get_character_material(wiki_name)
    if not pic_content and wiki_type_1 in {"all", "light_cone"}:
        pic_content = await srres.get_light_cone_overview(wiki_name)
    if not pic_content and wiki_type_1 in {"all", "relic_set"}:
        pic_content = await srres.get_relic_set_overview(wiki_name)
    if pic_content:
        msg_builder = MessageFactory([Image(pic_content)])
        await msg_builder.send(at_sender=True)
    await wiki_search.finish()
