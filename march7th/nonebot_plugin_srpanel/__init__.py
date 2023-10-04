from nonebot import get_driver, on_command, on_regex, require
from nonebot.adapters import Bot, Event
from nonebot.log import logger
from nonebot.params import RegexDict
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_saa")
require("nonebot_plugin_srres")
require("nonebot_plugin_srbind")
require("nonebot_plugin_datastore")

from nonebot_plugin_saa import Image, MessageFactory, Text

try:
    from march7th.nonebot_plugin_srbind import get_user_srbind
    from march7th.nonebot_plugin_srres import srres
except ModuleNotFoundError:
    from nonebot_plugin_srbind import get_user_srbind
    from nonebot_plugin_srres import srres

from .get_img import get_srpanel_img
from .models import (
    ScoreFile,
    get_srpanel_character,
    get_srpanel_player,
    update_score_file,
    update_srpanel,
)

__plugin_meta__ = PluginMetadata(
    name="StarRailPanel",
    description="崩坏：星穹铁道角色面板查询",
    usage="""\
更新面板: srpu
查看面板: xxxx面板
""",
    extra={
        "version": "1.0",
        "srhelp": """\
更新面板: srpu / 更新角色面板
查看面板: [u]xxxx[/u]面板
""",
    },
)

score: ScoreFile = {}

driver = get_driver()


@driver.on_startup
async def _():
    global score
    score_file = await update_score_file()
    if score_file:
        score = score_file
        logger.info("『崩坏：星穹铁道』遗器评分标准加载完成")
    else:
        logger.error("『崩坏：星穹铁道』遗器评分标准加载失败，请检查网络连接和插件配置")


srsupdate = on_command(
    "srsupdate", aliases={"更新星铁评分标准"}, permission=SUPERUSER, block=True
)


@srsupdate.handle()
async def _():
    global score
    msg_builder = MessageFactory([Text("开始更新『崩坏：星穹铁道』遗器评分标准")])
    await msg_builder.send()
    score_file = await update_score_file()
    if not score_file:
        msg_builder = MessageFactory([Text("『崩坏：星穹铁道』遗器评分标准更新失败，请检查网络连接和插件配置")])
    else:
        score = score_file
        msg_builder = MessageFactory([Text("『崩坏：星穹铁道』遗器评分标准更新完成")])
    await msg_builder.send()
    await srsupdate.finish()


srpu = on_command(
    "srpu",
    aliases={"更新角色面板", "更新星铁面板", "更新星铁角色面板", "星铁更新面板", "星铁更新角色面板"},
    priority=2,
    block=False,
)
srpanel = on_regex(r"(?P<name>\w{1,10})面板$", priority=9, block=False)


@srpu.handle()
async def _(bot: Bot, event: Event):
    user_list = await get_user_srbind(bot.self_id, event.get_user_id())
    if not user_list:
        msg = "未绑定SRUID，请使用`sruid [uid]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srpu.finish()
    sr_uid = user_list[0].sr_uid
    logger.info(f"正在更新SRUID『{sr_uid}』角色面板")
    msg_builder = MessageFactory([Text(f"正在更新SRUID『{sr_uid}』角色面板")])
    await msg_builder.send(at_sender=True)
    updated = await update_srpanel(bot.self_id, event.get_user_id(), sr_uid)
    if updated:
        msg = f"成功更新以下角色面板\n{updated}"
        msg_builder = MessageFactory([Text(msg)])
    else:
        msg_builder = MessageFactory([Text("角色面板更新失败，请稍后重试")])
    await msg_builder.send(at_sender=True)
    await srpu.finish()


@srpanel.handle()
async def _(bot: Bot, event: Event, regex_dict: dict = RegexDict()):
    name: str = regex_dict["name"] or ""
    if not name:
        await srpanel.finish()
    if name not in srres.NicknameRev:
        await srpanel.finish()
    cid = srres.NicknameRev[name]
    if len(cid) != 4:
        await srpanel.finish()
    user_list = await get_user_srbind(bot.self_id, event.get_user_id())
    if not user_list:
        msg = "未绑定SRUID，请使用`sruid [uid]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.send(at_sender=True)
        await srpanel.finish()
    sr_uid = user_list[0].sr_uid
    if str(cid).startswith("80"):
        cid = "8000"
    info = await get_srpanel_character(bot.self_id, event.get_user_id(), sr_uid, cid)
    if not info:
        name = srres.ResIndex["characters"][cid]["name"] if cid != "8000" else "开拓者"
        msg = f"未找到『{name}』的面板，请使用`srpu`更新面板"
        msg_builder = MessageFactory([Text(msg)])
        await msg_builder.send(at_sender=True)
        await srpanel.finish()
    player_info = await get_srpanel_player(bot.self_id, event.get_user_id(), sr_uid)
    if player_info:
        try:
            global score
            img = await get_srpanel_img(player_info, info, score)
        except Exception as e:
            img = None
            logger.warning(f"绘图出错：{e}")
            logger.exception(e)
    else:
        img = None
    if img:
        msg_builder = MessageFactory([Image(img)])
        await msg_builder.send()
    else:
        msg_builder = MessageFactory([Text("绘图出错，请使用`srpu`更新面板")])
        await msg_builder.send(at_sender=True)
    await srpanel.finish()
