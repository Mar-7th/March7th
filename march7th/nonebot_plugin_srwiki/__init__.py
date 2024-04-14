from typing import List

from nonebot.matcher import Matcher
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Event, Message
from nonebot import require, on_regex, on_command
from nonebot.params import RegexDict, CommandArg, ArgPlainText

require("nonebot_plugin_saa")
require("nonebot_plugin_srres")

from nonebot_plugin_saa import Image, MessageFactory

try:
    from march7th.nonebot_plugin_srres import srres
    from march7th.nonebot_plugin_srres.model.achievements import AchievementType
except ModuleNotFoundError:
    from nonebot_plugin_srres import srres
    from nonebot_plugin_srres.model.achievements import AchievementType

__plugin_meta__ = PluginMetadata(
    name="StarRailWiki",
    description="崩坏：星穹铁道百科",
    usage="""\
查询攻略图片: xxx(角色|光锥|遗器)(攻略|材料|测评)
查询成就详情: 查成就 xxx
隐藏成就列表: 查隐藏成就
""",
    extra={
        "version": "1.0",
        "srhelp": """\
查攻略: [u]xxx[/u]角色攻略
（支持 角色攻略/材料 光锥/遗器图鉴）
查成就: 查成就 [u]xxx[/u]
查隐藏成就列表: 查隐藏成就
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
async def _(event: Event, matcher: Matcher, regex_dict: dict = RegexDict()):
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
        matcher.stop_propagation()
        msg_builder = MessageFactory([Image(pic_content)])
        await msg_builder.finish(at_sender=not event.is_tome())
    await wiki_search.finish()


series_map = {
    "1": "我，开拓者",
    "2": "流光遗痕",
    "3": "通往群星的轨道",
    "4": "众秘探奇",
    "5": "与你同行的回忆",
    "6": "不屈者的荣光",
    "7": "战意奔涌",
    "8": "瞬息欢愉",
    "9": "果壳中的宇宙",
}


def remove_symbol(string: str):
    symbols = "•°…～、，：？！—（）《》「」ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ"
    for symbol in symbols:
        string = string.replace(symbol, "")
    return string


srac = on_command("srac", aliases={"查成就"}, block=True)


@srac.handle()
async def _(arg: Message = CommandArg()):
    name = arg.extract_plain_text().strip()
    if not name:
        await srac.finish(
            "请输入要查询的成就的关键字，如需查询隐藏成就，请使用『查隐藏成就』"
        )
    if achievement := srres.ResIndex["achievements"].get(name):
        message = f"{achievement.title}\n分类：{series_map[achievement.series_id]}\n描述：{achievement.desc}\n隐藏描述：{achievement.hide_desc}\n是否隐藏：{'是' if achievement.hide else '否'}"
        await srac.finish(message)
    results: List[AchievementType] = []
    for achievement in srres.ResIndex["achievements"].values():
        if name in remove_symbol(achievement.title):
            results.append(achievement)
    if not results:
        await srac.finish("未找到相关成就")
    if len(results) > 10:
        message = "找到以下成就，请输入更详细的名称查询：\n\n" + "\n".join(
            [achievement.title for achievement in results]
        )
        await srac.finish(message)
    message = "找到以下成就：\n\n" + "\n\n".join(
        [
            f"{'[隐藏]' if achievement.hide else ''}({series_map[achievement.series_id]}){achievement.title}: {achievement.desc} {achievement.hide_desc}"
            for achievement in results
        ]
    )
    await srac.finish(message)


srah = on_command("srah", aliases={"查隐藏成就"}, block=True)


@srah.handle()
async def _(matcher: Matcher, arg: Message = CommandArg()):
    name = arg.extract_plain_text().strip()
    if name in series_map:
        matcher.set_arg("key", arg)
    else:
        message = "请回复要查询的分类的序号\n" + "\n".join(
            [f"{k}: {v}" for k, v in series_map.items()]
        )
        await srah.send(message)


@srah.got("key")
async def _(key: str = ArgPlainText()):
    if key not in series_map:
        await srah.reject("序号错误，请重新输入")
    result: List[str] = []
    for achievement in srres.ResIndex["achievements"].values():
        if achievement.series_id == key and achievement.hide:
            result.append(achievement.title)
    message = f"{series_map[key]} 隐藏成就列表：\n\n" + "\n".join(result)
    await srah.finish(message)
