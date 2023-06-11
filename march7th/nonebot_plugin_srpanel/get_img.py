from io import BytesIO
from typing import Dict, List, Optional, Set

from PIL import Image, ImageEnhance
from pil_utils import BuildImage

try:
    from march7th.nonebot_plugin_srres import srres
except ModuleNotFoundError:
    from nonebot_plugin_srres import srres

from .models import CharacterInfo, PlayerInfo, ScoreFile

fontname = srres.get_font()
folder = srres.get_data_folder()

WHITE = (255, 255, 255)
GREEN = (85, 182, 44)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)

roman_dict = {5: "V", 4: "IV", 3: "III", 2: "II", 1: "I"}


async def get_image(file: str) -> Optional[Image.Image]:
    if file and await srres.cache(file):
        return Image.open(folder / file).convert("RGBA")
    return None


async def get_srpanel_img(
    player_info: PlayerInfo, character_info: CharacterInfo, score: ScoreFile
) -> Optional[BytesIO]:
    uid = player_info.uid
    time = character_info.time
    color = character_info.element.color if character_info.element else None
    name = character_info.name
    name = name.replace("{NICKNAME}", player_info.nickname)
    rank = character_info.rank
    level = character_info.level
    path = character_info.path.name if character_info.path else None
    element = character_info.element.name if character_info.element else None
    attributes = character_info.attributes
    additions = character_info.additions
    skill = character_info.skills
    light_cone = character_info.light_cone
    relic = character_info.relics
    relic_set = character_info.relic_sets
    preview_image = await get_image(character_info.preview)
    path_image = (
        await get_image(character_info.path.icon) if character_info.path else None
    )
    element_image = (
        await get_image(character_info.element.icon) if character_info.element else None
    )
    rank_icons = list(character_info.rank_icons)
    rank_images: List[Image.Image] = []
    for i in range(len(rank_icons)):
        rank_icon = await get_image(rank_icons[i])
        if rank_icon:
            rank_image = (
                BuildImage(rank_icon)
                .resize((64, 64))
                .draw_arc((0, 0, 64, 64), 0, 360, width=2, fill=WHITE)
                .image
            )
            if i >= rank:
                alpha = ImageEnhance.Brightness(rank_image)
                rank_image = alpha.enhance(0.3)
            rank_images.append(rank_image)
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
            (680, 228), str(path), fontname=fontname, fontsize=48, fill=WHITE
        )
    # element
    if element_image:
        element_image = element_image.resize((64, 64))
        image_res.paste(element_image, (820, 220), alpha=True)
        image_res.draw_text(
            (900, 228), str(element), fontname=fontname, fontsize=48, fill=str(color)
        )
    image_res.draw_text(
        (110, 728, 470, 808), name, max_fontsize=52, fontname=fontname, fill=WHITE
    )
    # rank
    y_index = 310
    for image in rank_images:
        image_res.paste(image, (500, y_index), alpha=True)
        y_index = y_index + 86
    # attributes
    attr_set: Set[str] = set()
    y_index = 305
    for attr in attributes:
        image_res.draw_rounded_rectangle(
            (600, y_index, 1000, y_index + 50), radius=15, outline=GRAY, width=2
        )
        image_res.draw_text(
            (620, y_index + 12),
            attr.name,
            fontname=fontname,
            fontsize=24,
            fill=WHITE,
        )
        image_res.draw_text(
            (760, y_index + 12),
            attr.display,
            fontname=fontname,
            fontsize=24,
            fill=WHITE,
        )
        for addi in additions:
            if addi.name == attr.name:
                image_res.draw_text(
                    (860, y_index + 12),
                    f"+{addi.display}",
                    fontname=fontname,
                    fontsize=24,
                    fill=GREEN,
                )
        attr_set.add(attr.name)
        y_index = y_index + 58
    for addi in additions:
        if y_index > 800:
            break
        name = str(addi.name)
        if name not in attr_set:
            name = name.replace("属性伤害提高", "增伤")
            image_res.draw_rounded_rectangle(
                (600, y_index, 1000, y_index + 50), radius=15, outline=GRAY, width=2
            )
            image_res.draw_text(
                (620, y_index + 12), name, fontname=fontname, fontsize=24, fill=WHITE
            )
            image_res.draw_text(
                (760, y_index + 12),
                addi.display,
                fontname=fontname,
                fontsize=24,
                fill=WHITE,
            )
            y_index = y_index + 58
    # skill
    x_index = 100
    if len(skill) > 5:
        skill = [skill[0], skill[1], skill[2], skill[3], skill[5]]
    for skill_item in skill:
        image_res.draw_rounded_rectangle(
            (x_index, 850, x_index + 172, 940), radius=15, outline=GRAY, width=2
        )
        item_icon = await get_image(skill_item.icon)
        if item_icon:
            item_icon = (
                BuildImage(item_icon)
                .resize((64, 64))
                .draw_arc((0, 0, 64, 64), 0, 360, width=2, fill=WHITE)
                .image
            )
            image_res.paste(item_icon, (x_index + 8, 863), alpha=True)
        name = str(skill_item.name)
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
            f"Lv.{int(skill_item.level)}",
            fontname=fontname,
            max_fontsize=36,
            fill=WHITE,
        )
        x_index = x_index + 182
    # light cone
    image_res.draw_rounded_rectangle(
        (100, 970, 500, 1150), radius=15, outline=GRAY, width=2
    )
    if light_cone:
        light_cone_image = await get_image(light_cone.icon)
        if light_cone_image:
            light_cone_image = light_cone_image.resize((156, 156))
            image_res.paste(light_cone_image, (110, 982), alpha=True)
        image_res.draw_text(
            (276, 990, 485, 1050),
            light_cone.name,
            fontname=fontname,
            max_fontsize=32,
            fill=WHITE,
        )
        image_res.draw_text(
            (286, 1050, 310, 1130),
            roman_dict[light_cone.rank],
            fontname=fontname,
            max_fontsize=48,
            fill=WHITE,
        )
        image_res.draw_text(
            (310, 1050, 350, 1130), "·", fontname=fontname, max_fontsize=48, fill=WHITE
        )
        image_res.draw_text(
            (350, 1050, 480, 1130),
            f"Lv.{light_cone.level}",
            fontname=fontname,
            max_fontsize=48,
            fill=WHITE,
        )
    else:
        image_res.draw_text(
            (100, 970, 500, 1150),
            "未装备光锥",
            fontname=fontname,
            max_fontsize=36,
            fill=WHITE,
        )
    # relic set
    y_index = 970
    for i in range(3):
        image_res.draw_rounded_rectangle(
            (520, y_index + 63 * i, 700, y_index + 63 * i + 54),
            radius=15,
            outline=GRAY,
            width=2,
        )
        if len(relic_set) > i:
            set_icon = relic_set[i].icon
            set_image = await get_image(set_icon)
            if set_image:
                set_image = set_image.resize((40, 40))
                image_res.paste(set_image, (535, y_index + 63 * i + 7), alpha=True)
            image_res.draw_text(
                (590, y_index + 63 * i, 680, y_index + 63 * i + 54),
                f"{relic_set[i].num}件套",
                fontname=fontname,
                max_fontsize=32,
                fill=WHITE,
            )
        else:
            image_res.draw_text(
                (540, y_index + 63 * i, 680, y_index + 63 * i + 54),
                "未激活套装",
                fontname=fontname,
                max_fontsize=32,
                fill=WHITE,
            )
    # relic score cal
    relic_score: Dict[str, float] = {}
    cid = character_info.id
    # relic
    for i in range(0, 6):
        x_index = 100 + 305 * (i % 3)
        y_index = 1180 + 320 * int(i / 3)
        image_res.draw_rounded_rectangle(
            (x_index, y_index, x_index + 290, y_index + 300),
            radius=15,
            outline=GRAY,
            width=2,
        )
        if i >= len(relic):
            image_res.draw_text(
                (x_index + 20, y_index + 20, x_index + 270, y_index + 280),
                "该位置未装备遗器",
                fontname=fontname,
                max_fontsize=36,
                fill=WHITE,
            )
        else:
            relic_info = relic[i]
            relic_type = relic_info.id[-1]
            relic_icon = relic_info.icon
            relic_image = await get_image(relic_icon)
            if relic_image:
                relic_image = relic_image.resize((64, 64))
                image_res.paste(relic_image, (x_index + 30, y_index + 30), alpha=True)
            image_res.draw_text(
                (x_index + 20, y_index + 120, x_index + 270, y_index + 156),
                relic_info.name,
                fontname=fontname,
                max_fontsize=36,
                fill=WHITE,
                stroke_fill=WHITE,
                stroke_ratio=0.03,
            )
            image_res.draw_text(
                (x_index + 110, y_index + 20, x_index + 270, y_index + 80),
                relic_info.main_affix.display if relic_info.main_affix else "",
                fontname=fontname,
                max_fontsize=52,
                fill=WHITE,
            )
            image_res.draw_text(
                (x_index + 94, y_index + 80, x_index + 130, y_index + 108),
                f"+{relic_info.level}",
                fontname=fontname,
                max_fontsize=24,
                fill=WHITE,
            )
            image_res.draw_text(
                (x_index + 130, y_index + 80, x_index + 270, y_index + 108),
                str(relic_info.main_affix.name).replace("属性伤害提高", "增伤")
                if relic_info.main_affix
                else "",
                fontname=fontname,
                max_fontsize=24,
                fill=WHITE,
            )
            y_index_item = y_index + 165
            relic_item_score = 0
            for affix in relic_info.sub_affix:
                FILL = (127, 127, 127)
                if cid in score.keys() and affix.type in score[cid].weight.keys():
                    relic_item_score += score[cid].weight[affix.type] * (
                        affix.count + 0.1 * affix.step
                    )
                    weight = 127 + int(128 * score[cid].weight[affix.type])
                    FILL = (weight, weight, weight)
                affix_image = await get_image(affix.icon)
                if affix_image:
                    affix_image = affix_image.resize((32, 32))
                    image_res.paste(
                        affix_image, (x_index + 30, y_index_item), alpha=True
                    )
                image_res.draw_text(
                    (x_index + 70, y_index_item),
                    affix.name,
                    fontname=fontname,
                    fontsize=24,
                    fill=FILL,
                )
                if affix.count > 1:
                    image_res.draw_text(
                        (x_index + 175, y_index_item + 10),
                        f"x{affix.count}",
                        fontname=fontname,
                        fontsize=14,
                        fill=FILL,
                    )
                image_res.draw_text(
                    (x_index + 200, y_index_item),
                    affix.display,
                    fontname=fontname,
                    fontsize=24,
                    fill=FILL,
                )
                y_index_item = y_index_item + 30
            if cid in score.keys() and relic_info.main_affix:
                if relic_type in {"1", "2"}:
                    relic_item_score = relic_item_score / score[cid].max
                else:
                    relic_item_score = (
                        relic_item_score / score[cid].max * 0.5
                        + score[cid].main[relic_type][relic_info.main_affix.type]
                        * ((relic_info.level + 1) / 16)
                        * 0.5
                    )
                relic_score[relic_info.id] = relic_item_score
    relic_score_all = format(sum(relic_score.values()) / 6 * 10, ".1f")
    # relic score
    image_res.draw_rounded_rectangle(
        (720, 970, 1000, 1150), radius=15, outline=GRAY, width=2
    )
    if not relic_score_all.startswith("0"):
        image_res.draw_text(
            (740, 1000, 980, 1080),
            f"{relic_score_all}/10",
            fontname=fontname,
            max_fontsize=72,
            fill=WHITE,
        )
    else:
        image_res.draw_text(
            (740, 1000, 980, 1080),
            "--",
            fontname=fontname,
            max_fontsize=72,
            fill=WHITE,
        )
    image_res.draw_text(
        (740, 1080, 980, 1130),
        "遗器评分",
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
