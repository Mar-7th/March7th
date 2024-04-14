from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot import require, on_command
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Bot, Event, Message

require("nonebot_plugin_saa")
require("nonebot_plugin_srbind")
require("nonebot_plugin_srres")

from nonebot_plugin_saa import Text, Image, MessageFactory

try:
    from march7th.nonebot_plugin_srbind import get_user_srbind
except ModuleNotFoundError:
    from nonebot_plugin_srbind import get_user_srbind

from .data_source import get_srgacha, update_srgacha

__plugin_meta__ = PluginMetadata(
    name="StarRailGacha",
    description="崩坏：星穹铁道抽卡记录查询",
    usage="""\
导入: 导入抽卡记录 [抽卡记录URL]
查看: 查看抽卡记录
""",
    extra={
        "version": "1.0",
        "srhelp": """\
导入: 导入抽卡记录 [u]抽卡记录URL[/u]
查看: 查看抽卡记录
""",
    },
)

srgu = on_command(
    "srgu",
    aliases={"导入抽卡记录", "更新抽卡记录", "导入星铁抽卡记录", "更新星铁抽卡记录"},
    priority=2,
    block=True,
)
srgc = on_command(
    "srgc",
    aliases={"查看抽卡记录", "查询抽卡记录", "查看星铁抽卡记录", "查询星铁抽卡记录"},
    priority=2,
    block=True,
)

HELP_MESSAGE = """\
请在命令后跟上抽卡记录链接，获取链接的教程:
docs.qq.com/doc/p/9c830f3e9398aaaf68d1eba225eead983947d2db"""


@srgu.handle()
async def _(bot: Bot, event: Event, arg: Message = CommandArg()):
    url = arg.extract_plain_text()
    if (
        not url
        or not url.startswith(
            "https://api-takumi.mihoyo.com/common/gacha_record/api/getGachaLog"
        )
        or "authkey=" not in url
    ):
        msg_builder = MessageFactory([Text(HELP_MESSAGE)])
        await msg_builder.finish(at_sender=not event.is_tome())
    user_list = await get_user_srbind(bot.self_id, event.get_user_id())
    if not user_list:
        msg = "未绑定SRUID，请使用`sruid [uid]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.finish(at_sender=not event.is_tome())
    sr_uid = user_list[0].sr_uid
    logger.info(f"开始更新SRUID『{sr_uid}』抽卡记录")
    msg_builder = MessageFactory([Text(f"开始更新SRUID『{sr_uid}』抽卡记录")])
    await msg_builder.send(at_sender=not event.is_tome())
    try:
        message = await update_srgacha(bot.self_id, event.get_user_id(), sr_uid, url)
    except Exception as e:
        logger.error(f"导入抽卡记录出错：{e}")
        message = "抽卡记录更新失败，请检查链接是否正确"
    msg_builder = MessageFactory([Text(message)])
    await msg_builder.finish(at_sender=not event.is_tome())


@srgc.handle()
async def _(bot: Bot, event: Event):
    user_list = await get_user_srbind(bot.self_id, event.get_user_id())
    if not user_list:
        msg = "未绑定SRUID，请使用`sruid [uid]`绑定或`srqr`扫码绑定"
        msg_builder = MessageFactory([Text(str(msg))])
        await msg_builder.finish(at_sender=not event.is_tome())
    sr_uid = user_list[0].sr_uid
    try:
        img = await get_srgacha(bot.self_id, event.get_user_id(), sr_uid)
    except Exception as e:
        img = None
        logger.warning(f"绘图出错：{e}")
        logger.exception(e)
    if img is None:
        msg_builder = MessageFactory([Text("请先使用 导入抽卡记录 命令导入抽卡记录")])
        await msg_builder.finish(at_sender=not event.is_tome())
    msg_builder = MessageFactory([Image(img)])
    await msg_builder.finish()
