from io import BytesIO
from pathlib import Path
from typing import Dict, Generator, List, Optional, TypeVar

import httpx
from PIL import Image
from pil_utils import BuildImage

IMG_PATH = Path(__file__).parent / "images"

rarity_4_bg = Image.open(IMG_PATH / "rarity_4_bg.png").convert("RGBA")
rarity_5_bg = Image.open(IMG_PATH / "rarity_5_bg.png").convert("RGBA")
item_bg = Image.open(IMG_PATH / "item_bg.png").convert("RGBA")

BACKGROUND = (248, 248, 248)
GRAY1 = (200, 200, 200)
GRAY2 = (100, 100, 100)
GRAY3 = (75, 75, 75)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

fontname = "HYRunYuan-65W"
fallback_fonts = [
    "Sarasa Mono SC",
    "Source Han Sans SC",
    "Microsoft YaHei",
    "Noto Sans SC",
    "Noto Sans CJK JP",
    "WenQuanYi Micro Hei",
]

element_icons = {
    "ice": Image.open(IMG_PATH / "icon_ice.png").convert("RGBA"),
    "fire": Image.open(IMG_PATH / "icon_fire.png").convert("RGBA"),
    "imaginary": Image.open(IMG_PATH / "icon_imaginary.png").convert("RGBA"),
    "quantum": Image.open(IMG_PATH / "icon_quantum.png").convert("RGBA"),
    "lightning": Image.open(IMG_PATH / "icon_thunder.png").convert("RGBA"),
    "wind": Image.open(IMG_PATH / "icon_wind.png").convert("RGBA"),
    "physical": Image.open(IMG_PATH / "icon_physical.png").convert("RGBA"),
}

T = TypeVar("T")


def wrap_list(lst: List[T], n: int) -> Generator[List[T], None, None]:
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def level_fmt(level: int) -> str:
    return f"Lv.0{level}" if level < 10 else f"Lv.{level}"


async def get_icon(url: str) -> Image.Image:
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return Image.open(BytesIO(resp.content)).convert("RGBA")


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
    equips: Dict[int, Optional[str]] = {}  # 装备信息 dict

    details = sr_avatar_info["avatar_list"]
    for detail in details:
        equip = detail["equip"]
        equips[detail["id"]] = equip["icon"] if equip is not None else None  # type: ignore

    # 绘制图片
    image_bg = BuildImage.new("RGBA", (800, 360), BACKGROUND)

    big_text_font_args = {
        "fontsize": 48,
        "fill": GRAY3,
        "fontname": fontname,
        "weight": "bold",
        "fallback_fonts": fallback_fonts,
    }
    text_font_args = {
        "fontsize": 30,
        "fill": GRAY2,
        "fontname": fontname,
        "weight": "bold",
        "fallback_fonts": fallback_fonts,
    }
    small_text_font_args = {
        "fontsize": 24,
        "fill": GRAY2,
        "fontname": fontname,
        "weight": "bold",
        "fallback_fonts": fallback_fonts,
    }
    num_font_args = {
        "fontsize": 36,
        "fill": GRAY3,
        "fontname": fontname,
        "weight": "bold",
        "fallback_fonts": fallback_fonts,
    }
    small_num_font_args = {
        "fontsize": 24,
        "fill": WHITE,
        "fontname": fontname,
        "weight": "bold",
        "fallback_fonts": fallback_fonts,
    }

    # 写Nickname
    image_bg.draw_text((100, 30), nickname, **big_text_font_args)
    # 写UID
    image_bg.draw_text((100, 100), f"UID {sr_uid}", **text_font_args)
    # 写基本信息
    image_bg.draw_line((50, 150, 750, 150), fill=GRAY1, width=2)
    image_bg.draw_text((100, 180), "活跃天数", **small_text_font_args)  # 活跃天数
    image_bg.draw_text((250, 170), str(active_days), **num_font_args)  # 活跃天数
    image_bg.draw_text((100, 230), "解锁角色", **small_text_font_args)  # 解锁角色
    image_bg.draw_text((250, 220), str(avater_num), **num_font_args)  # 解锁角色
    image_bg.draw_text((100, 280), "达成成就", **small_text_font_args)  # 达成成就
    image_bg.draw_text((250, 270), str(achievement_num), **num_font_args)  # 达成成就
    image_bg.draw_text((400, 180), "宝箱开启", **small_text_font_args)  # 宝箱开启
    image_bg.draw_text((550, 170), str(chest_num), **num_font_args)  # 宝箱开启
    image_bg.draw_text((400, 230), "开拓等级", **small_text_font_args)  # 开拓等级
    image_bg.draw_text((550, 220), str(level), **num_font_args)  # 开拓等级
    image_bg.draw_text((400, 280), "忘却之庭", **small_text_font_args)  # 忘却之庭
    image_bg.draw_text((550, 280), str(abyss_process), **small_text_font_args)  # 忘却之庭
    image_bg.draw_line((50, 325, 750, 325), fill=GRAY1, width=2)

    # 角色部分 每五个一组
    lines = []
    for five_avatars in wrap_list(avatars, 5):
        line = BuildImage.new("RGBA", (800, 200), BACKGROUND)
        x_index = 70
        for avatar in five_avatars:
            item_image = BuildImage(
                (rarity_4_bg if avatar["rarity"] == 4 else rarity_5_bg).copy()
            )
            char_icon = await get_icon(avatar["icon"])
            element_icon = element_icons[avatar["element"]]
            item_image.paste(char_icon, (4, 8), alpha=True)
            item_image.paste(element_icon, (81, 10), alpha=True)
            if equip := equips[avatar["id"]]:
                equip_icon = (await get_icon(equip)).resize((48, 48))
                item_image.paste(item_bg.copy(), alpha=True)
                item_image.paste(equip_icon, (9, 80), alpha=True)
            item_image.draw_text(
                (28, 130), level_fmt(avatar["level"]), **small_num_font_args
            )
            line.paste(item_image, (x_index, 0))
            x_index += 135
        lines.append(line)

    # 绘制总图
    image_res = BuildImage.new("RGBA", (800, 360 + len(lines) * 200), BACKGROUND)
    image_res.paste(image_bg, (0, 0))

    y_index = 360
    for line in lines:
        image_res.paste(line, (0, y_index), alpha=True)
        y_index += 200

    image_res.draw_rectangle(
        (10, 10, 800 - 10, 360 + len(lines) * 200 - 10), outline=GRAY1, width=3
    )
    image_res.draw_rectangle(
        (20, 20, 800 - 20, 360 + len(lines) * 200 - 20), outline=GRAY1
    )

    return image_res.save_png()
