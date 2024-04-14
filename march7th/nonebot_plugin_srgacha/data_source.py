import json
import asyncio
from io import BytesIO
from urllib.parse import parse_qs, urlparse, urlencode
from typing import Any, Dict, List, TypeVar, Optional, Generator

from PIL import Image
from nonebot import get_driver
from pil_utils import BuildImage
from pydantic import ValidationError
from sqlalchemy import select, update
from nonebot.compat import type_validate_python
from nonebot_plugin_datastore import create_session
from nonebot.drivers import Request, HTTPClientMixin

try:
    from march7th.nonebot_plugin_srres import srres
except ModuleNotFoundError:
    from nonebot_plugin_srres import srres

from .model import GachaLog, GachaLogItem, UserGachaLog, GachaLogResponse

fontname = srres.get_font()
folder = srres.get_data_folder()

# Resident characters and light cones
RESIDENT = {
    "1003",
    "1004",
    "1101",
    "1104",
    "1107",
    "1209",
    "1211",
    "23000",
    "23002",
    "23003",
    "23004",
    "23005",
    "23012",
    "23013",
}

driver = get_driver()
if not isinstance(driver, HTTPClientMixin):
    raise RuntimeError(
        f"当前驱动配置 {driver} 无法进行 HTTP 请求，请在 DRIVER 配置项末尾添加 +~httpx"
    )

T = TypeVar("T")


def wrap_list(lst: List[T], n: int) -> Generator[List[T], None, None]:
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


async def get_icon(id: str) -> Optional[Image.Image]:
    icon = await srres.get_icon(id=id)
    if icon:
        return Image.open(icon).convert("RGBA")
    return None


async def request(url: str) -> Optional[Dict]:
    request = Request(
        "GET",
        url,
        timeout=10,
    )
    response = await driver.request(request)
    try:
        data = json.loads(response.content or "{}")
        return data
    except (json.JSONDecodeError, KeyError):
        return None


async def fetch_gacha_log(gacha_url: str, gacha_type: str) -> Dict[str, GachaLogItem]:
    parsed_url = urlparse(gacha_url)
    query_params = parse_qs(parsed_url.query)
    query_params["authkey_ver"] = ["1"]
    query_params["sign_type"] = ["2"]
    query_params["lang"] = ["zh-cn"]
    query_params["game_biz"] = ["hkrpg_cn"]
    query_params["size"] = ["20"]
    query_params["gacha_type"] = [gacha_type]
    url_base = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    query_string = urlencode(query_params, doseq=True)
    full_gacha_log: Dict[str, GachaLogItem] = {}
    while True:
        query_string = urlencode(query_params, doseq=True)
        url = f"{url_base}?{query_string}"
        response = await request(url)
        data = type_validate_python(GachaLogResponse, response)
        if len(data.data.list) == 0:
            break
        gacha_log = {i.id: i for i in data.data.list}
        full_gacha_log.update(gacha_log)
        query_params["end_id"] = [data.data.list[-1].id]
        await asyncio.sleep(0.3)
    return full_gacha_log


async def get_gacha(bot_id: str, user_id: str, sr_uid: str) -> Optional[UserGachaLog]:
    """
    Get gacha from database
    """
    statement = select(UserGachaLog).where(
        UserGachaLog.bot_id == bot_id,
        UserGachaLog.user_id == user_id,
        UserGachaLog.sr_uid == sr_uid,
    )
    async with create_session() as session:
        record = (await session.scalars(statement)).one_or_none()
    return record


async def save_gacha(gacha: UserGachaLog):
    """
    Save gacha to database
    """
    select_gacha = await get_gacha(gacha.bot_id, gacha.user_id, gacha.sr_uid)
    async with create_session() as session:
        if select_gacha:
            statement = (
                update(UserGachaLog)
                .where(UserGachaLog.id == select_gacha.id)
                .values(gacha=gacha.gacha)
            )
            await session.execute(statement)
        else:
            session.add(gacha)
        await session.commit()


async def update_srgacha(bot_id: str, user_id: str, sr_uid: str, url: str) -> str:
    """
    Update user gacha log by url
    """
    # Get orgin data
    user_gacha = await get_gacha(bot_id, user_id, sr_uid)
    if user_gacha:
        try:
            origin_data = type_validate_python(GachaLog, user_gacha.gacha)
        except ValidationError:
            origin_data = GachaLog()
    else:
        origin_data = GachaLog()
    # Fetch new data
    new_data = GachaLog()
    new_data.common = await fetch_gacha_log(url, "1")
    new_data.beginner = await fetch_gacha_log(url, "2")
    new_data.character_event = await fetch_gacha_log(url, "11")
    new_data.light_cone_event = await fetch_gacha_log(url, "12")
    # Merge data
    new_data.common.update(origin_data.common)
    new_data.beginner.update(origin_data.beginner)
    new_data.character_event.update(origin_data.character_event)
    new_data.light_cone_event.update(origin_data.light_cone_event)
    # Calculate changes
    common_add = len(new_data.common.keys()) - len(origin_data.common.keys())
    beginner_add = len(new_data.beginner.keys()) - len(origin_data.beginner.keys())
    character_event_add = len(new_data.character_event.keys()) - len(
        origin_data.character_event.keys()
    )
    light_cone_event_add = len(new_data.common.keys()) - len(origin_data.common.keys())
    # Save and return message
    if (
        common_add == 0
        and beginner_add == 0
        and character_event_add == 0
        and light_cone_event_add == 0
    ):
        ret_msg = "没有新的抽卡记录"
    else:
        # Save data
        new_user_gacha = UserGachaLog(
            bot_id=bot_id, user_id=user_id, sr_uid=sr_uid, gacha=new_data.dict()
        )
        await save_gacha(new_user_gacha)
        ret_msg = "抽卡记录已更新，增加了"
        ret_msg += f" {common_add} 条常驻池记录，" if common_add else ""
        ret_msg += f" {beginner_add} 条新手池记录，" if common_add else ""
        ret_msg += f" {character_event_add} 条角色池记录，" if common_add else ""
        ret_msg += f" {light_cone_event_add} 条光锥池记录，" if common_add else ""
        ret_msg = ret_msg.rstrip("，")
    ret_msg += "\n"
    ret_msg += "当前共有"
    ret_msg += f" {len(new_data.common.keys())} 条常驻池记录，"
    ret_msg += f" {len(new_data.beginner.keys())} 条新手池记录，"
    ret_msg += f" {len(new_data.character_event.keys())} 条角色池记录，"
    ret_msg += f" {len(new_data.light_cone_event.keys())} 条光锥池记录"
    ret_msg += "\n"
    ret_msg += "可回复『查看抽卡记录』查看"
    return ret_msg


def analyze_gacha(gacha: Dict[str, GachaLogItem]) -> Dict[str, Any]:
    result = {}
    gacha_list = list(gacha.values())
    gacha_sorted = sorted(gacha_list, key=lambda x: x.id)
    counter_5_up = 0
    counter_5 = 0
    counter_4 = 0
    counter_5_up_list = []
    counter_5_list = []
    items = {}
    for item in gacha_sorted:
        if item.rank_type == "5":
            items[item.id] = item.dict()
            items[item.id]["cost"] = counter_5
            items[item.id]["is_up"] = False if item.item_id in RESIDENT else True
            if item.item_id in RESIDENT:
                counter_5_up += 1
            else:
                counter_5_up_list.append(counter_5_up)
                counter_5_up = 0
            counter_4 += 1
            counter_5_list.append(counter_5)
            counter_5 = 0
        elif item.rank_type == "4":
            counter_5_up += 1
            counter_5 += 1
            counter_4 = 0
        else:
            counter_5_up += 1
            counter_5 += 1
            counter_4 += 1
    result["items"] = dict(sorted(items.items(), reverse=True))
    result["avg_5_up_cost"] = (
        sum(counter_5_up_list) / len(counter_5_up_list) if counter_5_up_list else 0
    )
    result["avg_5_cost"] = (
        sum(counter_5_list) / len(counter_5_list) if counter_5_list else 0
    )
    result["counter_5_up"] = counter_5_up
    result["counter_5"] = counter_5
    result["counter_4"] = counter_4
    return result


async def get_srgacha(bot_id: str, user_id: str, sr_uid: str) -> Optional[BytesIO]:
    """
    Get user gacha log image
    """
    # Get gacha data
    user_gacha = await get_gacha(bot_id, user_id, sr_uid)
    if user_gacha is None:
        return None
    # Parse to model
    try:
        gacha = type_validate_python(GachaLog, user_gacha.gacha)
    except ValidationError:
        return None
    # Get star5 items
    star5_c = [item for item in gacha.common.values() if item.rank_type == "5"]
    star5_b = [item for item in gacha.beginner.values() if item.rank_type == "5"]
    star5_ce = [
        item for item in gacha.character_event.values() if item.rank_type == "5"
    ]
    star5_lce = [
        item for item in gacha.light_cone_event.values() if item.rank_type == "5"
    ]
    # Get analyze result
    common = analyze_gacha(gacha.common)
    beginner = analyze_gacha(gacha.beginner)
    character_event = analyze_gacha(gacha.character_event)
    light_cone_event = analyze_gacha(gacha.light_cone_event)
    count_5_total = (
        common["counter_5"]
        + beginner["counter_5"]
        + character_event["counter_5"]
        + light_cone_event["counter_5"]
    )
    # Calculate numerical values
    num_c = len(gacha.common)
    num_b = len(gacha.beginner)
    num_ce = len(gacha.character_event)
    num_lce = len(gacha.light_cone_event)
    num_star5_c = len(star5_c)
    num_star5_b = len(star5_b)
    num_star5_ce = len(star5_ce)
    num_star5_lce = len(star5_lce)
    num_total = num_c + num_b + num_ce + num_lce
    num_star5_total = num_star5_c + num_star5_b + num_star5_ce + num_star5_lce
    avg_star5_cost = (
        round((num_total - count_5_total) / num_star5_total, 1)
        if num_star5_total
        else 0
    )
    avg_star5_cost_c = (
        round((num_c - common["counter_5"]) / num_star5_c, 1) if num_star5_c else 0
    )
    avg_star5_cost_b = (
        round((num_b - beginner["counter_5"]) / num_star5_b, 1) if num_star5_b else 0
    )
    avg_star5_cost_ce = (
        round((num_ce - character_event["counter_5"]) / num_star5_ce, 1)
        if num_star5_ce
        else 0
    )
    avg_star5_cost_lce = (
        round((num_lce - light_cone_event["counter_5"]) / num_star5_lce, 1)
        if num_star5_lce
        else 0
    )
    # Draw image
    # Overall
    image_overall = BuildImage.new("RGBA", (1160, 320), "black")
    # Nickname
    image_overall.draw_text(
        (60, 50), "抽卡记录", fontsize=72, fontname=fontname, fill="white"
    )
    # UID
    image_overall.draw_text(
        (800, 85), f"UID {sr_uid}", fontsize=36, fontname=fontname, fill="white"
    )
    image_overall.draw_line((50, 150, 1110, 150), fill="gray", width=2)
    # 总抽卡数
    image_overall.draw_text(
        (50, 240, 210, 270),
        "总抽卡数",
        max_fontsize=24,
        fontname=fontname,
        fill="white",
    )
    image_overall.draw_text(
        (50, 180, 210, 230),
        str(num_total),
        max_fontsize=48,
        fontname=fontname,
        fill="white",
    )
    # 总五星数
    image_overall.draw_text(
        (350, 240, 510, 270),
        "总五星数",
        max_fontsize=24,
        fontname=fontname,
        fill="white",
    )
    image_overall.draw_text(
        (350, 180, 510, 230),
        str(num_star5_total),
        max_fontsize=48,
        fontname=fontname,
        fill="white",
    )
    # 平均五星抽数
    image_overall.draw_text(
        (650, 240, 790, 270),
        "平均五星抽数",
        max_fontsize=24,
        fontname=fontname,
        fill="white",
    )
    image_overall.draw_text(
        (650, 180, 790, 230),
        str(avg_star5_cost),
        max_fontsize=48,
        fontname=fontname,
        fill="white",
    )
    # 抽卡评价
    comment = (
        "未知"
        if avg_star5_cost == 0
        else (
            "欧"
            if avg_star5_cost <= 50
            else (
                "吉" if avg_star5_cost <= 60 else "中" if avg_star5_cost <= 70 else "非"
            )
        )
    )
    image_overall.draw_text(
        (930, 180, 1090, 270),
        comment,
        max_fontsize=56,
        fontname=fontname,
        fill="white",
    )
    image_overall.draw_line((50, 300, 1110, 300), fill="gray", width=2)
    # Character event lines
    lines_character_event = []
    for six_avatars in wrap_list(list(character_event["items"].values()), 6):
        line = BuildImage.new("RGBA", (1160, 240), "black")
        x_index = 50
        for avatar in six_avatars:
            item_image = BuildImage.new("RGBA", (160, 180), "black")
            char_icon = await get_icon(str(avatar["item_id"]))
            if char_icon:
                char_icon = BuildImage(char_icon).resize((100, 100)).circle()
                item_image.paste(char_icon, (30, 15), alpha=True)
            item_image.draw_text(
                (120, 10, 150, 40),
                str(avatar["cost"]),
                fontsize=24,
                fontname=fontname,
                fill="white",
            )
            item_image.draw_text(
                (10, 10, 40, 40),
                "UP" if avatar["is_up"] else "",
                fontsize=24,
                fontname=fontname,
                fill="white",
            )
            item_image.draw_text(
                (30, 125, 130, 155),
                str(avatar["name"]),
                fontsize=22,
                fontname=fontname,
                fill="white",
            )
            item_image.draw_rounded_rectangle(
                (0, 0, 160, 160),
                radius=10,
                outline="gray",
                width=2,
            )
            line.paste(item_image, (x_index, 0))
            x_index += 180
        lines_character_event.append(line)
    # Light cone event lines
    lines_light_cone_event = []
    for six_avatars in wrap_list(list(light_cone_event["items"].values()), 6):
        line = BuildImage.new("RGBA", (1160, 240), "black")
        x_index = 50
        for avatar in six_avatars:
            item_image = BuildImage.new("RGBA", (160, 180), "black")
            char_icon = await get_icon(str(avatar["item_id"]))
            if char_icon:
                char_icon = BuildImage(char_icon).resize((100, 100)).circle()
                item_image.paste(char_icon, (30, 15), alpha=True)
            item_image.draw_text(
                (120, 10, 150, 40),
                str(avatar["cost"]),
                fontsize=24,
                fontname=fontname,
                fill="white",
            )
            item_image.draw_text(
                (10, 10, 40, 40),
                "UP" if avatar["is_up"] else "",
                fontsize=24,
                fontname=fontname,
                fill="white",
            )
            item_image.draw_text(
                (30, 125, 130, 155),
                str(avatar["name"]),
                fontsize=22,
                fontname=fontname,
                fill="white",
            )
            item_image.draw_rounded_rectangle(
                (0, 0, 160, 160),
                radius=10,
                outline="gray",
                width=2,
            )
            line.paste(item_image, (x_index, 0))
            x_index += 180
        lines_light_cone_event.append(line)
    # Stellar warp lines
    lines_common = []
    for six_avatars in wrap_list(list(common["items"].values()), 6):
        line = BuildImage.new("RGBA", (1160, 240), "black")
        x_index = 50
        for avatar in six_avatars:
            item_image = BuildImage.new("RGBA", (160, 180), "black")
            char_icon = await get_icon(str(avatar["item_id"]))
            if char_icon:
                char_icon = BuildImage(char_icon).resize((100, 100)).circle()
                item_image.paste(char_icon, (30, 15), alpha=True)
            item_image.draw_text(
                (120, 10, 150, 40),
                str(avatar["cost"]),
                fontsize=24,
                fontname=fontname,
                fill="white",
            )
            # item_image.draw_text(
            #     (10, 10, 40, 40),
            #     "UP" if avatar["is_up"] else "",
            #     fontsize=24,
            #     fontname=fontname,
            #     fill="white",
            # )
            item_image.draw_text(
                (30, 125, 130, 155),
                str(avatar["name"]),
                fontsize=22,
                fontname=fontname,
                fill="white",
            )
            item_image.draw_rounded_rectangle(
                (0, 0, 160, 160),
                radius=10,
                outline="gray",
                width=2,
            )
            line.paste(item_image, (x_index, 0))
            x_index += 180
        lines_common.append(line)
    # Departure warp lines
    lines_beginner = []
    for six_avatars in wrap_list(list(beginner["items"].values()), 6):
        line = BuildImage.new("RGBA", (1160, 240), "black")
        x_index = 50
        for avatar in six_avatars:
            item_image = BuildImage.new("RGBA", (160, 180), "black")
            char_icon = await get_icon(str(avatar["item_id"]))
            if char_icon:
                char_icon = BuildImage(char_icon).resize((100, 100)).circle()
                item_image.paste(char_icon, (30, 15), alpha=True)
            item_image.draw_text(
                (120, 10, 150, 40),
                str(avatar["cost"]),
                fontsize=24,
                fontname=fontname,
                fill="white",
            )
            # item_image.draw_text(
            #     (10, 10, 40, 40),
            #     "UP" if avatar["is_up"] else "",
            #     fontsize=24,
            #     fontname=fontname,
            #     fill="white",
            # )
            item_image.draw_text(
                (30, 125, 130, 155),
                str(avatar["name"]),
                fontsize=22,
                fontname=fontname,
                fill="white",
            )
            item_image.draw_rounded_rectangle(
                (0, 0, 160, 160),
                radius=10,
                outline="gray",
                width=2,
            )
            line.paste(item_image, (x_index, 0))
            x_index += 180
        lines_beginner.append(line)
    # Draw image
    total_height = 740 + 200 * (
        len(lines_common)
        + len(lines_beginner)
        + len(lines_character_event)
        + len(lines_light_cone_event)
    )
    image_res = BuildImage.new("RGBA", (1160, total_height), "black")
    image_res.paste(image_overall, (0, 0))
    y_index = 320
    # 角色卡池
    image_res.draw_text(
        (50, y_index, 210, y_index + 80),
        "角色卡池",
        max_fontsize=32,
        fontname=fontname,
        fill="white",
    )
    # 抽卡数
    image_res.draw_text(
        (350, y_index + 50, 510, y_index + 80),
        "抽卡数",
        max_fontsize=30,
        fontname=fontname,
        fill="white",
    )
    image_res.draw_text(
        (350, y_index, 510, y_index + 50),
        str(num_ce),
        max_fontsize=48,
        fontname=fontname,
        fill="white",
    )
    # 平均五星抽数
    image_res.draw_text(
        (650, y_index + 50, 790, y_index + 80),
        "平均五星抽数",
        max_fontsize=30,
        fontname=fontname,
        fill="white",
    )
    image_res.draw_text(
        (650, y_index, 790, y_index + 50),
        str(avg_star5_cost_ce),
        max_fontsize=48,
        fontname=fontname,
        fill="white",
    )
    # 未出五星
    image_res.draw_text(
        (930, y_index + 50, 1090, y_index + 80),
        "未出五星",
        max_fontsize=30,
        fontname=fontname,
        fill="white",
    )
    image_res.draw_text(
        (930, y_index, 1090, y_index + 50),
        str(character_event["counter_5"]),
        max_fontsize=48,
        fontname=fontname,
        fill="white",
    )
    y_index += 100
    for line in lines_character_event:
        image_res.paste(line, (0, y_index), alpha=True)
        y_index += 200
    image_res.draw_line((50, y_index - 20, 1110, y_index - 20), fill="gray", width=2)
    # 光锥卡池
    image_res.draw_text(
        (50, y_index, 210, y_index + 80),
        "光锥卡池",
        max_fontsize=32,
        fontname=fontname,
        fill="white",
    )
    # 抽卡数
    image_res.draw_text(
        (350, y_index + 50, 510, y_index + 80),
        "抽卡数",
        max_fontsize=30,
        fontname=fontname,
        fill="white",
    )
    image_res.draw_text(
        (350, y_index, 510, y_index + 50),
        str(num_lce),
        max_fontsize=48,
        fontname=fontname,
        fill="white",
    )
    # 平均五星抽数
    image_res.draw_text(
        (650, y_index + 50, 790, y_index + 80),
        "平均五星抽数",
        max_fontsize=30,
        fontname=fontname,
        fill="white",
    )
    image_res.draw_text(
        (650, y_index, 790, y_index + 50),
        str(avg_star5_cost_lce),
        max_fontsize=48,
        fontname=fontname,
        fill="white",
    )
    # 未出五星
    image_res.draw_text(
        (930, y_index + 50, 1090, y_index + 80),
        "未出五星",
        max_fontsize=30,
        fontname=fontname,
        fill="white",
    )
    image_res.draw_text(
        (930, y_index, 1090, y_index + 50),
        str(light_cone_event["counter_5"]),
        max_fontsize=48,
        fontname=fontname,
        fill="white",
    )
    y_index += 100
    for line in lines_light_cone_event:
        image_res.paste(line, (0, y_index), alpha=True)
        y_index += 200
    image_res.draw_line((50, y_index - 20, 1110, y_index - 20), fill="gray", width=2)
    # 常驻卡池
    image_res.draw_text(
        (50, y_index, 210, y_index + 80),
        "常驻卡池",
        max_fontsize=32,
        fontname=fontname,
        fill="white",
    )
    # 抽卡数
    image_res.draw_text(
        (350, y_index + 50, 510, y_index + 80),
        "抽卡数",
        max_fontsize=30,
        fontname=fontname,
        fill="white",
    )
    image_res.draw_text(
        (350, y_index, 510, y_index + 50),
        str(num_c),
        max_fontsize=48,
        fontname=fontname,
        fill="white",
    )
    # 平均五星抽数
    image_res.draw_text(
        (650, y_index + 50, 790, y_index + 80),
        "平均五星抽数",
        max_fontsize=30,
        fontname=fontname,
        fill="white",
    )
    image_res.draw_text(
        (650, y_index, 790, y_index + 50),
        str(avg_star5_cost_c),
        max_fontsize=48,
        fontname=fontname,
        fill="white",
    )
    # 未出五星
    image_res.draw_text(
        (930, y_index + 50, 1090, y_index + 80),
        "未出五星",
        max_fontsize=30,
        fontname=fontname,
        fill="white",
    )
    image_res.draw_text(
        (930, y_index, 1090, y_index + 50),
        str(common["counter_5"]),
        max_fontsize=48,
        fontname=fontname,
        fill="white",
    )
    y_index += 100
    for line in lines_common:
        image_res.paste(line, (0, y_index), alpha=True)
        y_index += 200
    image_res.draw_line((50, y_index - 20, 1110, y_index - 20), fill="gray", width=2)
    # 新手卡池
    image_res.draw_text(
        (50, y_index, 210, y_index + 80),
        "新手卡池",
        max_fontsize=32,
        fontname=fontname,
        fill="white",
    )
    # 抽卡数
    image_res.draw_text(
        (350, y_index + 50, 510, y_index + 80),
        "抽卡数",
        max_fontsize=30,
        fontname=fontname,
        fill="white",
    )
    image_res.draw_text(
        (350, y_index, 510, y_index + 50),
        str(num_b),
        max_fontsize=48,
        fontname=fontname,
        fill="white",
    )
    # 平均五星抽数
    image_res.draw_text(
        (650, y_index + 50, 790, y_index + 80),
        "平均五星抽数",
        max_fontsize=30,
        fontname=fontname,
        fill="white",
    )
    image_res.draw_text(
        (650, y_index, 790, y_index + 50),
        str(avg_star5_cost_b),
        max_fontsize=48,
        fontname=fontname,
        fill="white",
    )
    # 未出五星
    image_res.draw_text(
        (930, y_index + 50, 1090, y_index + 80),
        "未出五星",
        max_fontsize=30,
        fontname=fontname,
        fill="white",
    )
    image_res.draw_text(
        (930, y_index, 1090, y_index + 50),
        str(beginner["counter_5"]),
        max_fontsize=48,
        fontname=fontname,
        fill="white",
    )
    y_index += 100
    for line in lines_beginner:
        image_res.paste(line, (0, y_index), alpha=True)
        y_index += 200

    image_res.draw_rectangle(
        (10, 10, 1160 - 10, total_height - 10), outline="gray", width=6
    )
    image_res.draw_rectangle(
        (20, 20, 1160 - 20, total_height - 20), outline="white", width=2
    )

    return image_res.save_png()
