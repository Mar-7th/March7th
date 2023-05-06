from io import BytesIO
from typing import Dict, Generator, List, Optional, TypeVar

from PIL import Image
from pil_utils import BuildImage

try:
    from march7th.nonebot_plugin_srres import srres
except ModuleNotFoundError:
    from nonebot_plugin_srres import srres

BACKGROUND = (248, 248, 248)
GRAY1 = (200, 200, 200)
GRAY2 = (100, 100, 100)
GRAY3 = (75, 75, 75)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

STAR5 = (194, 152, 99)
STAR4 = (128, 85, 194)

fontname = "HYRunYuan-65W"

T = TypeVar("T")


def wrap_list(lst: List[T], n: int) -> Generator[List[T], None, None]:
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def level_fmt(level: int) -> str:
    return f"Lv.0{level}" if level < 10 else f"Lv.{level}"


def get_icon(name: str) -> Optional[Image.Image]:
    icon = srres.icon(name)
    if icon:
        return Image.open(icon).convert("RGBA")
    return None


def get_element_icon(name: str) -> Optional[Image.Image]:
    icon = srres.icon_element(name)
    if icon:
        return Image.open(icon).convert("RGBA")
    return None


async def get_srinfo_img(
    sr_uid, sr_basic_info, sr_index, sr_avatar_info
) -> Optional[BytesIO]:
    nickname = sr_basic_info["nickname"]  # 昵称
    level = sr_basic_info["level"]  # 等级

    stats = sr_index["stats"]  # 统计信息 dict
    active_days = stats["active_days"]  # 活跃天数
    avater_num = stats["avatar_num"]  # 角色数量
    achievement_num = stats["achievement_num"]  # 成就数量
    chest_num = stats["chest_num"]  # 宝箱数量
    abyss_process = stats["abyss_process"]  # 深渊进度

    avatars = sr_index["avatar_list"]  # 角色信息 list
    equips: Dict[int, Dict[str, str]] = {}  # 装备信息 dict

    details = sr_avatar_info["avatar_list"]
    for detail in details:
        equip = detail["equip"]
        if equip is not None:
            equips[detail["id"]] = {}
            equips[detail["id"]]["name"] = equip["name"]
            equips[detail["id"]]["rank"] = equip["rank"]
            equips[detail["id"]]["level"] = equip["level"]

    # 绘制图片
    image_bg = BuildImage.new("RGBA", (800, 380), BACKGROUND)

    image_bg.draw_text(
        (60, 50), nickname, fontsize=48, fontname=fontname, fill=GRAY3
    )  # Nickname
    image_bg.draw_text(
        (60, 110), f"UID {sr_uid}", fontsize=24, fontname=fontname, fill=GRAY3
    )  # UID
    image_bg.draw_text(
        (600, 50, 700, 140), str(level), max_fontsize=72, fontname=fontname, fill=GRAY3
    )  # 开拓等级

    image_bg.draw_line((50, 150, 750, 150), fill=GRAY1, width=2)

    image_bg.draw_text(
        (50, 240, 210, 270), "活跃天数", max_fontsize=24, fontname=fontname, fill=GRAY2
    )  # 活跃天数
    image_bg.draw_text(
        (50, 180, 210, 230),
        str(active_days),
        max_fontsize=48,
        fontname=fontname,
        fill=GRAY3,
    )  # 活跃天数
    image_bg.draw_text(
        (230, 240, 390, 270), "解锁角色", max_fontsize=24, fontname=fontname, fill=GRAY2
    )  # 解锁角色
    image_bg.draw_text(
        (230, 180, 390, 230),
        str(avater_num),
        max_fontsize=48,
        fontname=fontname,
        fill=GRAY3,
    )  # 解锁角色
    image_bg.draw_text(
        (410, 240, 550, 270), "达成成就", max_fontsize=24, fontname=fontname, fill=GRAY2
    )  # 达成成就
    image_bg.draw_text(
        (410, 180, 550, 230),
        str(achievement_num),
        max_fontsize=48,
        fontname=fontname,
        fill=GRAY3,
    )  # 达成成就
    image_bg.draw_text(
        (570, 240, 730, 270), "宝箱开启", max_fontsize=24, fontname=fontname, fill=GRAY2
    )  # 宝箱开启
    image_bg.draw_text(
        (570, 180, 730, 230),
        str(chest_num),
        max_fontsize=48,
        fontname=fontname,
        fill=GRAY3,
    )  # 宝箱开启

    image_bg.draw_line((50, 290, 750, 290), fill=GRAY1, width=2)

    image_bg.draw_text(
        (50, 310, 210, 340), "忘却之庭", max_fontsize=24, fontname=fontname, fill=GRAY2
    )  # 忘却之庭
    image_bg.draw_text(
        (300, 310, 700, 340),
        str(abyss_process),
        max_fontsize=36,
        fontname=fontname,
        fill=GRAY3,
    )  # 忘却之庭

    image_bg.draw_line((50, 360, 750, 360), fill=GRAY1, width=2)

    # 角色部分 每五个一组
    lines = []
    for five_avatars in wrap_list(avatars, 4):
        line = BuildImage.new("RGBA", (800, 240), BACKGROUND)
        x_index = 50
        for avatar in five_avatars:
            item_image = BuildImage.new("RGBA", (160, 240), BACKGROUND)
            rank = avatar["rank"]
            rarity = avatar["rarity"]
            char_icon = get_icon(avatar["name"])
            element_icon = get_element_icon(avatar["element"])
            if char_icon:
                char_icon = (
                    BuildImage(char_icon)
                    .resize((100, 100))
                    .circle()
                    .draw_arc((0, 0, 100, 100), 0, 360, width=2, fill=GRAY2)
                )
                if rarity == 5:
                    char_icon.draw_arc((0, 0, 100, 100), 0, 360, width=3, fill=STAR5)
                else:
                    char_icon.draw_arc((0, 0, 100, 100), 0, 360, width=3, fill=STAR4)
                item_image.paste(char_icon, (30, 30), alpha=True)
            item_image.draw_text(
                (30, 130, 130, 170),
                level_fmt(avatar["level"]),
                fontsize=36,
                fontname=fontname,
                fill=GRAY2,
            )
            if element_icon:
                element_icon = element_icon.resize((28, 28))
                item_image.paste(element_icon, (116, 16), alpha=True)
            if rank > 0:
                item_image.draw_rounded_rectangle(
                    (16, 16, 36, 36), outline=GRAY2, radius=5, width=2
                )
                item_image.draw_text(
                    (16, 16, 36, 36),
                    str(rank),
                    max_fontsize=24,
                    fontname=fontname,
                    fill=GRAY2,
                )
            if avatar["id"] in equips:
                equip = equips[avatar["id"]]
                equip_icon = get_icon(equip["name"])
                if equip_icon:
                    equip_icon = equip_icon.resize((56, 56))
                    item_image.paste(equip_icon, (20, 170), alpha=True)
                    item_image.draw_rounded_rectangle(
                        (94, 174, 114, 194), outline=GRAY2, radius=5, width=2
                    )
                    item_image.draw_text(
                        (94, 174, 114, 194),
                        str(equip["rank"]),
                        fontname=fontname,
                        fill=GRAY2,
                    )
                    item_image.draw_text(
                        (80, 198, 130, 226),
                        level_fmt(int(equip["level"])),
                        max_fontsize=24,
                        fontname=fontname,
                        fill=GRAY2,
                    )
            else:
                item_image.draw_text(
                    (30, 180, 130, 220), "未装备光锥", fontname=fontname, fill=GRAY2
                )
            item_image.draw_rounded_rectangle(
                (0, 0, 160, 240), radius=10, outline=GRAY2, width=3
            )
            line.paste(item_image, (x_index, 0))
            x_index += 180
        lines.append(line)

    # 绘制总图
    image_res = BuildImage.new("RGBA", (800, 400 + len(lines) * 260), BACKGROUND)
    image_res.paste(image_bg, (0, 0))

    y_index = 380
    for line in lines:
        image_res.paste(line, (0, y_index), alpha=True)
        y_index += 260

    image_res.draw_rectangle(
        (10, 10, 800 - 10, 400 + len(lines) * 260 - 10), outline=GRAY3, width=6
    )
    image_res.draw_rectangle(
        (20, 20, 800 - 20, 400 + len(lines) * 260 - 20), outline=GRAY2, width=2
    )

    return image_res.save_png()
