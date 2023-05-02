from base64 import b64encode
from io import BytesIO
from pathlib import Path
from typing import Dict, Generator, List, Optional, TypeVar

import httpx
from PIL import Image, ImageDraw, ImageFont

IMG_PATH = Path(__file__).parent / "images"
FONT_PATH = Path(__file__).parent / "fonts"
FONT_FILE_PATH = FONT_PATH / "SDK_SC_Web.ttf"

bg1 = Image.open(IMG_PATH / "bg1.png")
bg2 = Image.open(IMG_PATH / "bg2.png")
bg3 = Image.open(IMG_PATH / "bg3.png")
user_avatar = Image.open(IMG_PATH / "200101.png").resize((220, 220)).convert("RGBA")
char_bg_4 = Image.open(IMG_PATH / "rarity4_bg.png").convert("RGBA")
char_bg_5 = Image.open(IMG_PATH / "rarity5_bg.png").convert("RGBA")
circle = Image.open(IMG_PATH / "char_weapon_bg.png").convert("RGBA")

bg_color = (248, 248, 248)
white_color = (255, 255, 255)
color_color = (40, 18, 7)
first_color = (22, 8, 31)

elements = {
    "ice": Image.open(IMG_PATH / "IconNatureColorIce.png").convert("RGBA"),
    "fire": Image.open(IMG_PATH / "IconNatureColorFire.png").convert("RGBA"),
    "imaginary": Image.open(IMG_PATH / "IconNatureColorImaginary.png").convert("RGBA"),
    "quantum": Image.open(IMG_PATH / "IconNatureColorQuantum.png").convert("RGBA"),
    "lightning": Image.open(IMG_PATH / "IconNatureColorThunder.png").convert("RGBA"),
    "wind": Image.open(IMG_PATH / "IconNatureColorWind.png").convert("RGBA"),
    "physical": Image.open(IMG_PATH / "IconNaturePhysical.png").convert("RGBA"),
}


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_FILE_PATH), size=size)


def level_fmt(level: int) -> str:
    return f"Lv.0{level}" if level < 10 else f"Lv.{level}"


T = TypeVar("T")


def wrap_list(lst: List[T], n: int) -> Generator[List[T], None, None]:
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


async def get_icon(url: str) -> Image.Image:
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return Image.open(BytesIO(resp.content)).convert("RGBA")


def img2b64(img) -> str:
    """图片转 base64"""
    buf = BytesIO()
    img.save(buf, format="PNG")
    base64_str = "base64://" + b64encode(buf.getvalue()).decode()
    return base64_str


async def get_srinfo_img(
    sr_uid, sr_basic_info, sr_index, sr_avatar_info
) -> Optional[str]:
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
    img_bg1 = bg1.copy()
    bg1_draw = ImageDraw.Draw(img_bg1)

    # 写Nickname
    bg1_draw.text((400, 85), nickname, font=font(36), fill=white_color, anchor="mm")
    # 写UID
    bg1_draw.text(
        (400, 165),
        f"UID {sr_uid}",
        font=font(30),
        fill=white_color,
        anchor="mm",
    )
    # 贴头像
    img_bg1.paste(user_avatar, (286, 213), mask=user_avatar)

    # 写基本信息
    bg1_draw.text(
        (143, 590),
        str(active_days),
        font=font(36),
        fill=white_color,
        anchor="mm",
    )  # 活跃天数
    bg1_draw.text(
        (270, 590),
        str(avater_num),
        font=font(36),
        fill=white_color,
        anchor="mm",
    )  # 解锁角色
    bg1_draw.text(
        (398, 590),
        str(achievement_num),
        font=font(36),
        fill=white_color,
        anchor="mm",
    )  # 达成成就
    bg1_draw.text(
        (525, 590),
        str(chest_num),
        font=font(36),
        fill=white_color,
        anchor="mm",
    )  # 战利品开启
    bg1_draw.text(
        (666, 590), str(level), font=font(36), fill=white_color, anchor="mm"
    )  # 开拓等级

    # 画忘却之庭
    bg1_draw.text(
        (471, 722),
        abyss_process,
        font=font(30),
        fill=first_color,
        anchor="mm",
    )

    # 角色部分 每五个一组
    lines = []
    for five_avatars in wrap_list(avatars, 5):
        line = bg2.copy()
        x = 70
        for avatar in five_avatars:
            char_bg = (char_bg_4 if avatar["rarity"] == 4 else char_bg_5).copy()
            char_draw = ImageDraw.Draw(char_bg)
            char_icon = await get_icon(avatar["icon"])
            element_icon = elements[avatar["element"]]

            char_bg.paste(char_icon, (4, 8), mask=char_icon)
            char_bg.paste(element_icon, (81, 10), mask=element_icon)

            if equip := equips[avatar["id"]]:
                char_bg.paste(circle, (0, 0), mask=circle)
                equip_icon = (await get_icon(equip)).resize((48, 48))
                char_bg.paste(equip_icon, (9, 80), mask=equip_icon)

            char_draw.text(
                (60, 146),
                level_fmt(avatar["level"]),
                font=font(24),
                fill=color_color,
                anchor="mm",
            )

            line.paste(char_bg, (x, 0))
            x += 135
        lines.append(line)

    # 绘制总图
    img = Image.new("RGBA", (800, 880 + len(lines) * 200), bg_color)
    img.paste(img_bg1, (0, 0))

    y = 810
    for line in lines:
        img.paste(line, (0, y), mask=line)
        y += 200

    img.paste(bg3, (0, len(lines) * 200 + 810))

    return img2b64(img)
