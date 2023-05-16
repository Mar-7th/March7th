from io import BytesIO
from typing import Optional

from PIL import Image, ImageEnhance
from pil_utils import BuildImage

try:
    from march7th.nonebot_plugin_srres import srres
except ModuleNotFoundError:
    from nonebot_plugin_srres import srres

fontname = srres.get_font()
folder = srres.get_data_folder()

WHITE = (255, 255, 255)
GREEN = (85, 182, 44)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)

roman_dict = {5: "V", 4: "IV", 3: "III", 2: "II", 1: "I"}


async def get_image(file: str) -> Optional[Image.Image]:
    if await srres.cache(file):
        return Image.open(folder / file).convert("RGBA")
    return None


async def get_srpanel_img(player_info, character_info) -> Optional[BytesIO]:
    uid = player_info["uid"]
    time = character_info["time"]
    color = character_info["color"]
    name = character_info["name"]
    name.replace("{NICKNAME}", player_info["name"])
    level = character_info["level"]
    path = character_info["path"]
    element = character_info["element"]
    promotion = character_info["promotion"]
    property = character_info["property"]
    skill = character_info["skill"]
    light_cone = character_info["light_cone"]
    relic = character_info["relic"]
    relic_set = character_info["relic_set"]
    preview_image = await get_image(character_info["preview"])
    path_image = await get_image(character_info["path_icon"])
    element_image = await get_image(character_info["element_icon"])
    rank_icons = list(character_info["rank_icons"])
    for i in range(len(rank_icons)):
        rank_icon = await get_image(rank_icons[i]["icon"])
        if rank_icon:
            rank_icon = (
                BuildImage(rank_icon)
                .resize((64, 64))
                .draw_arc((0, 0, 64, 64), 0, 360, width=2, fill=WHITE)
                .image
            )
        rank_icons[i]["image"] = rank_icon
        if rank_icon and not rank_icons[i]["unlock"]:
            alpha = ImageEnhance.Brightness(rank_icons[i]["image"])
            rank_icons[i]["image"] = alpha.enhance(0.3)
    image_res = BuildImage.new("RGBA", (1080, 1900), BLACK)
    image_res.draw_text((100, 100), f"角色面板", fontsize=92, fontname=fontname, fill=WHITE)
    image_res.draw_text(
        (100, 220), f"UID:{uid}", fontsize=48, fontname=fontname, fill=WHITE
    )
    # level
    image_res.draw_text(
        (800, 120), f"Lv.{level}", fontname=fontname, fontsize=72, fill=WHITE
    )
    # preview
    image_res.draw_rounded_rectangle(
        (100, 300, 480, 818), radius=30, outline=GRAY, width=3
    )
    if preview_image:
        preview_image = preview_image.resize((374, 512))
        image_res.paste(preview_image, (103, 303), alpha=True)
    # path
    if path_image:
        path_image = path_image.resize((64, 64))
        image_res.paste(path_image, (600, 220), alpha=True)
        image_res.draw_text(
            (680, 228), path, fontname=fontname, fontsize=48, fill=WHITE
        )
    # element
    if element_image:
        element_image = element_image.resize((64, 64))
        image_res.paste(element_image, (820, 220), alpha=True)
        image_res.draw_text(
            (900, 228), element, fontname=fontname, fontsize=48, fill=color
        )
    image_res.draw_text(
        (110, 728, 470, 808), name, max_fontsize=52, fontname=fontname, fill=WHITE
    )
    # rank
    y_index = 310
    for rank in rank_icons:
        rank_image = rank["image"]
        if rank_image:
            image_res.paste(rank_image, (500, y_index), alpha=True)
            y_index = y_index + 86
    # property
    prom_set = set()
    y_index = 305
    for prom in promotion:
        image_res.draw_rounded_rectangle(
            (600, y_index, 1000, y_index + 50), radius=15, outline=GRAY, width=2
        )
        image_res.draw_text(
            (620, y_index + 12),
            prom["name"],
            fontname=fontname,
            fontsize=24,
            fill=WHITE,
        )
        image_res.draw_text(
            (760, y_index + 12),
            prom["value"],
            fontname=fontname,
            fontsize=24,
            fill=WHITE,
        )
        for prop in property:
            if prop["name"] == prom["name"]:
                image_res.draw_text(
                    (860, y_index + 12),
                    f'(+{prop["value"]})',
                    fontname=fontname,
                    fontsize=24,
                    fill=GREEN,
                )
        prom_set.add(prom["name"])
        y_index = y_index + 58
    for prop in property:
        if y_index > 800:
            break
        name = str(prop["name"])
        if name not in prom_set:
            name = name.replace("属性伤害提高", "增伤")
            image_res.draw_rounded_rectangle(
                (600, y_index, 1000, y_index + 50), radius=15, outline=GRAY, width=2
            )
            image_res.draw_text(
                (620, y_index + 12), name, fontname=fontname, fontsize=24, fill=WHITE
            )
            image_res.draw_text(
                (760, y_index + 12),
                prop["value"],
                fontname=fontname,
                fontsize=24,
                fill=WHITE,
            )
            y_index = y_index + 58
    # skill
    x_index = 100
    for skill_item in skill:
        image_res.draw_rounded_rectangle(
            (x_index, 850, x_index + 172, 940), radius=15, outline=GRAY, width=2
        )
        item_icon = await get_image(skill_item["icon"])
        if item_icon:
            item_icon = (
                BuildImage(item_icon)
                .resize((64, 64))
                .draw_arc((0, 0, 64, 64), 0, 360, width=2, fill=WHITE)
                .image
            )
            image_res.paste(item_icon, (x_index + 8, 863), alpha=True)
        name = str(skill_item["name"])
        if len(name) > 5:
            name = name[:3] + "..."
        image_res.draw_text(
            (x_index + 80, 860, x_index + 162, 890),
            name,
            fontname=fontname,
            max_fontsize=30,
            fill=WHITE,
        )
        image_res.draw_text(
            (x_index + 80, 890, x_index + 162, 930),
            f'Lv.{int(skill_item["level"])}',
            fontname=fontname,
            max_fontsize=36,
            fill=WHITE,
        )
        x_index = x_index + 182
    # light cone
    image_res.draw_rounded_rectangle(
        (100, 970, 540, 1150), radius=15, outline=GRAY, width=2
    )
    if light_cone:
        light_cone_image = await get_image(light_cone["icon"])
        if light_cone_image:
            light_cone_image = light_cone_image.resize((156, 156))
            image_res.paste(light_cone_image, (110, 982), alpha=True)
        image_res.draw_text(
            (276, 990, 525, 1050),
            light_cone["name"],
            fontname=fontname,
            max_fontsize=32,
            fill=WHITE,
        )
        image_res.draw_text(
            (286, 1050, 310, 1130),
            roman_dict[light_cone["rank"]],
            fontname=fontname,
            max_fontsize=48,
            fill=WHITE,
        )
        image_res.draw_text(
            (310, 1050, 370, 1130), "·", fontname=fontname, max_fontsize=48, fill=WHITE
        )
        image_res.draw_text(
            (370, 1050, 520, 1130),
            f'Lv.{light_cone["level"]}',
            fontname=fontname,
            max_fontsize=48,
            fill=WHITE,
        )
    else:
        image_res.draw_text(
            (100, 970, 540, 1150),
            "未装备光锥",
            fontname=fontname,
            max_fontsize=36,
            fill=WHITE,
        )
    # relic score
    image_res.draw_rounded_rectangle(
        (560, 970, 1000, 1150), radius=15, outline=GRAY, width=2
    )
    image_res.draw_text(
        (580, 1000, 980, 1080), "🥰", fontname=fontname, max_fontsize=72, fill=WHITE
    )
    image_res.draw_text(
        (580, 1080, 980, 1130),
        "遗器评级（暂无）",
        fontname=fontname,
        max_fontsize=36,
        fill=WHITE,
    )
    # relic
    for i in range(1, 6):
        x_index = 100 + 305 * (i % 3)
        y_index = 1180 + 320 * int(i / 3)
        image_res.draw_rounded_rectangle(
            (x_index, y_index, x_index + 290, y_index + 300),
            radius=15,
            outline=GRAY,
            width=2,
        )
        type_str = str(i)
        if type_str not in relic:
            image_res.draw_text(
                (x_index + 20, y_index + 20, x_index + 270, y_index + 280),
                "该位置未装备遗器",
                fontname=fontname,
                max_fontsize=36,
                fill=WHITE,
            )
        else:
            relic_info = relic[type_str]
            relic_icon = relic_info["icon"]
            relic_image = await get_image(relic_icon)
            if relic_image:
                relic_image = relic_image.resize((64, 64))
                image_res.paste(relic_image, (x_index + 20, y_index + 35), alpha=True)
            image_res.draw_text(
                (x_index + 20, y_index + 120, x_index + 270, y_index + 156),
                relic_info["name"],
                fontname=fontname,
                max_fontsize=36,
                fill=WHITE,
                stroke_fill=WHITE,
                stroke_ratio=0.03,
            )
            image_res.draw_text(
                (x_index + 110, y_index + 20),
                relic_info["main_property"]["value"],
                fontname=fontname,
                fontsize=52,
                fill=WHITE,
            )
            image_res.draw_text(
                (x_index + 110, y_index + 80),
                str(relic_info["main_property"]["name"]).replace("属性伤害提高", "增伤"),
                fontname=fontname,
                fontsize=24,
                fill=WHITE,
            )
            y_index_item = y_index + 165
            for prop in relic_info["sub_property"]:
                image_res.draw_text(
                    (x_index + 30, y_index_item),
                    prop["name"],
                    fontname=fontname,
                    fontsize=24,
                    fill=WHITE,
                )
                image_res.draw_text(
                    (x_index + 200, y_index_item),
                    prop["value"],
                    fontname=fontname,
                    fontsize=24,
                    fill=WHITE,
                )
                y_index_item = y_index_item + 30
    # relic set
    y_index = 1180
    for i in range(3):
        image_res.draw_rounded_rectangle(
            (100, y_index + 105 * i, 390, y_index + 105 * i + 90),
            radius=15,
            outline=GRAY,
            width=2,
        )
        if len(relic_set) >= i:
            set_icon = relic_set[i]["icon"]
            set_image = await get_image(set_icon)
            if set_image:
                set_image = set_image.resize((64, 64))
                image_res.paste(set_image, (130, y_index + 105 * i + 13), alpha=True)
            image_res.draw_text(
                (220, y_index + 105 * i, 370, y_index + 105 * i + 90),
                relic_set[i]["desc"],
                fontname=fontname,
                max_fontsize=36,
                fill=WHITE,
            )
    image_res.draw_text(
        (80, 1820, 1020, 1870),
        f"Created by Mar-7th/March7th & Mihomo API @ {time}",
        fontname=fontname,
        max_fontsize=36,
        fill=WHITE,
    )
    return image_res.save_png()
