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
    properties = character_info.properties
    skills = character_info.skills
    skill_trees = character_info.skill_trees
    light_cone = character_info.light_cone
    relic = character_info.relics
    relic_set = character_info.relic_sets
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
    image_res = BuildImage.new("RGBA", (1720, 1650), BLACK)
    # title
    title_image_bg = await get_image("icon/logo/bg.png")
    title_image = await get_image("icon/logo/cn.png")
    if title_image_bg and title_image:
        title_image_bg = title_image_bg.resize((300, 150))
        image_res.paste(title_image_bg, (700, 40), alpha=True)
        title_image = title_image.resize((300, 150))
        image_res.paste(title_image, (700, 40), alpha=True)
    image_res.draw_text((100, 180), f"角色面板", fontsize=92, fontname=fontname, fill=WHITE)
    # uid
    image_res.draw_text(
        (550, 224), f"UID:{uid}", fontsize=48, fontname=fontname, fill=WHITE
    )
    # path
    path_image = (
        await get_image(character_info.path.icon) if character_info.path else None
    )
    if path_image:
        path_image = path_image.resize((64, 64))
        image_res.paste(path_image, (950, 220), alpha=True)
        image_res.draw_text(
            (1030, 228), str(path), fontname=fontname, fontsize=48, fill=WHITE
        )
    # element
    element_image = (
        await get_image(character_info.element.icon) if character_info.element else None
    )
    if element_image:
        element_image = element_image.resize((64, 64))
        image_res.paste(element_image, (1170, 220), alpha=True)
        image_res.draw_text(
            (1250, 228), str(element), fontname=fontname, fontsize=48, fill=WHITE
        )
        image_res.draw_text(
            (1250, 228), str(element), fontname=fontname, fontsize=48, fill=f"{color}88"
        )
    # level
    image_res.draw_text(
        (1420, 200),
        f"Lv.{level}",
        fontname=fontname,
        fontsize=72,
        fill=WHITE,
    )
    # preview
    image_res.draw_rounded_rectangle(
        (100, 300, 480, 818), radius=30, outline=GRAY, width=3
    )
    preview_image = await get_image(character_info.preview)
    if preview_image:
        preview_image = preview_image.resize((374, 512))
        image_res.paste(preview_image, (103, 303), alpha=True)
    image_res.draw_text(
        (110, 728, 470, 808), name, max_fontsize=52, fontname=fontname, fill=WHITE
    )
    # rank
    y_index = 310
    for image in rank_images:
        image_res.paste(image, (500, y_index), alpha=True)
        y_index = y_index + 86
    # attributes
    x_index = 600
    y_index = 305
    attr_set: Set[str] = set()
    for attr in attributes:
        image_res.draw_rounded_rectangle(
            (x_index, y_index, x_index + 400, y_index + 50),
            radius=15,
            outline=GRAY,
            width=2,
        )
        image_res.draw_text(
            (x_index + 20, y_index + 12),
            attr.name,
            fontname=fontname,
            fontsize=24,
            fill=WHITE,
        )
        # basic value
        if not attr.percent:
            image_res.draw_text(
                (x_index + 250, y_index + 6),
                attr.display,
                fontname=fontname,
                fontsize=20,
                fill=WHITE,
            )
        # boost value
        boost = 0
        for addi in additions:
            if addi.name == attr.name:
                boost = addi.value
                image_res.draw_text(
                    (x_index + 300, y_index + 20),
                    f"+{addi.display}",
                    fontname=fontname,
                    fontsize=20,
                    fill=GREEN,
                )
        # total value
        total = attr.value + boost
        total_str = (
            str(int(total)) if not attr.percent else f"{format(total*100,'.1f')}%"
        )
        image_res.draw_text(
            (x_index + 160, y_index + 12),
            total_str,
            fontname=fontname,
            fontsize=24,
            fill=WHITE,
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
                (x_index, y_index, x_index + 400, y_index + 50),
                radius=15,
                outline=GRAY,
                width=2,
            )
            image_res.draw_text(
                (x_index + 20, y_index + 12),
                name,
                fontname=fontname,
                fontsize=24,
                fill=WHITE,
            )
            image_res.draw_text(
                (x_index + 220, y_index + 12),
                addi.display,
                fontname=fontname,
                fontsize=24,
                fill=WHITE,
            )
            y_index = y_index + 58
    # skill
    x_index = 100
    y_index = 850
    y_step = 100
    for i in range(4):
        y_item = y_index + y_step * i
        y_next = y_item + y_step
        image_res.draw_rounded_rectangle(
            (x_index, y_item, x_index + 270, y_next - 10),
            radius=15,
            outline=GRAY,
            width=2,
        )
        if len(skills) < i:
            image_res.draw_text(
                (x_index + 10, y_item + 10, x_index + 260, y_item + 80),
                f"无法获取技能信息",
                fontname=fontname,
                max_fontsize=36,
                fill=WHITE,
            )
        item_icon = await get_image(skills[i].icon)
        if item_icon:
            item_icon = (
                BuildImage(item_icon)
                .resize((64, 64))
                .draw_arc((0, 0, 64, 64), 0, 360, width=2, fill=WHITE)
                .image
            )
            image_res.paste(item_icon, (x_index + 15, y_item + 13), alpha=True)
        name = str(skills[i].name)
        if len(name) > 6:
            name = name[:5] + "..."
        image_res.draw_text(
            (x_index + 80, y_item + 10, x_index + 260, y_item + 40),
            name,
            fontname=fontname,
            max_fontsize=30,
            fill=WHITE,
        )
        image_res.draw_text(
            (x_index + 80, y_item + 40, x_index + 260, y_item + 80),
            f"Lv.{int(skills[i].level)}",
            fontname=fontname,
            max_fontsize=36,
            fill=WHITE,
        )
    # skill tree
    x_index = 380
    y_index = 850
    y_step = 100
    point_groups: List[Set] = []
    image_res.draw_rounded_rectangle(
        (x_index, y_index, x_index + 350, y_index + y_step * 4 - 10),
        radius=15,
        outline=GRAY,
        width=2,
    )
    for i in range(4, 8):
        y_item = y_index + y_step * (i - 4)
        y_next = y_item + y_step
        if len(skill_trees) <= i:
            break
        point_groups.append({skill_trees[i].id})
        item_icon = await get_image(skill_trees[i].icon)
        if item_icon:
            item_icon = (
                BuildImage(item_icon)
                .resize((64, 64))
                .draw_arc((0, 0, 64, 64), 0, 360, width=2, fill=WHITE)
                .image
            )
            if skill_trees[i].level == 0:
                alpha = ImageEnhance.Brightness(item_icon)
                item_icon = alpha.enhance(0.3)
            image_res.paste(item_icon, (x_index + 20, y_item + 13), alpha=True)
    x_index = 420
    x_step = 80
    point_groups[0] = {None}
    for i in range(8, 18):
        if len(skill_trees) <= i:
            break
        for j, group in enumerate(point_groups):
            if skill_trees[i].parent in group:
                group.add(skill_trees[i].id)
                x_offset = len(group) - 1
                item_icon = await get_image(skill_trees[i].icon)
                if item_icon:
                    item_icon = (
                        BuildImage(item_icon)
                        .resize((48, 48))
                        .draw_arc((0, 0, 48, 48), 0, 360, width=2, fill=WHITE)
                        .image
                    )
                    if skill_trees[i].level == 0:
                        alpha = ImageEnhance.Brightness(item_icon)
                        item_icon = alpha.enhance(0.3)
                    if not (x_offset == 1 and skill_trees[i].parent is None):
                        image_res.draw_line(
                            (
                                x_index + x_offset * x_step - 20,
                                y_index + j * y_step + 45,
                                x_index + x_offset * x_step - 10,
                                y_index + j * y_step + 45,
                            ),
                            fill=WHITE,
                            width=2,
                        )
                    image_res.paste(
                        item_icon,
                        (x_index + x_offset * x_step, y_index + j * y_step + 21),
                        alpha=True,
                    )
                break
    # light cone
    x_index = 750
    y_index = 850
    image_res.draw_rounded_rectangle(
        (x_index, y_index, x_index + 250, y_index + 390),
        radius=15,
        outline=GRAY,
        width=2,
    )
    if light_cone:
        light_cone_image = await get_image(light_cone.icon)
        if light_cone_image:
            light_cone_image = light_cone_image.resize((200, 200))
            image_res.paste(light_cone_image, (x_index + 25, y_index + 20), alpha=True)
        image_res.draw_text(
            (x_index + 20, y_index + 220, x_index + 230, y_index + 270),
            light_cone.name,
            fontname=fontname,
            max_fontsize=36,
            fill=WHITE,
        )
        image_res.draw_text(
            (x_index + 20, y_index + 270, x_index + 230, y_index + 310),
            f"叠影 {roman_dict[light_cone.rank]} 阶",
            fontname=fontname,
            max_fontsize=24,
            fill=WHITE,
        )
        image_res.draw_text(
            (x_index + 20, y_index + 310, x_index + 230, y_index + 370),
            f"Lv.{light_cone.level}",
            fontname=fontname,
            max_fontsize=48,
            fill=WHITE,
        )
    else:
        image_res.draw_text(
            (x_index + 20, y_index + 20, x_index + 230, y_index + 370),
            "未装备光锥",
            fontname=fontname,
            max_fontsize=36,
            fill=WHITE,
        )
    # properties
    x_index = 100
    y_index = 1260
    x_step = 180
    y_step = 70
    image_res.draw_rounded_rectangle(
        (x_index, y_index, x_index + 900, y_index + 230),
        radius=15,
        outline=GRAY,
        width=2,
    )
    for i, prop in enumerate(properties):
        if i >= 15:
            break
        x_item = x_index + i % 5 * x_step
        y_item = y_index + i // 5 * y_step
        prop_image = await get_image(prop.icon)
        if prop_image:
            prop_image = prop_image.resize((52, 52))
            image_res.paste(prop_image, (x_item + 20, y_item + 18), alpha=True)
        image_res.draw_text(
            (x_item + 80, y_item + 20, x_item + 170, y_item + 70),
            prop.display,
            fontname=fontname,
            max_fontsize=32,
            fill=WHITE,
        )
    # relic score cal
    relic_score: Dict[str, float] = {}
    cid = character_info.id
    # relic
    for i in range(0, 6):
        x_index = 1040 + 305 * (i // 3)
        y_index = 300 + 320 * (i % 3)
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
                (x_index + 130, y_index + 20, x_index + 270, y_index + 80),
                relic_info.main_affix.display if relic_info.main_affix else "--",
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
                relic_item_score = (
                    relic_item_score / score[cid].max * 0.5
                    + score[cid].main[relic_type][relic_info.main_affix.type]
                    * ((relic_info.level + 1) / 16)
                    * 0.5
                )
                relic_score[relic_info.id] = relic_item_score * 10
                score_disp = format(relic_score[relic_info.id], ".1f")
                image_res.draw_text(
                    (x_index + 98, y_index + 20, x_index + 128, y_index + 48),
                    score_disp,
                    fontname=fontname,
                    max_fontsize=16,
                    fill=WHITE,
                )
    relic_score_all = format(sum(relic_score.values()) / 6, ".1f")
    # relic set
    x_index = 1040
    y_index = 1260
    y_step = 80
    for i in range(3):
        y_item = y_index + y_step * i
        y_next = y_item + y_step
        image_res.draw_rounded_rectangle(
            (
                x_index,
                y_item,
                x_index + 340,
                y_next - 10,
            ),
            radius=15,
            outline=GRAY,
            width=2,
        )
        if len(relic_set) > i:
            set_icon = relic_set[i].icon
            set_image = await get_image(set_icon)
            if set_image:
                set_image = set_image.resize((40, 40))
                image_res.paste(set_image, (x_index + 30, y_item + 15), alpha=True)
            image_res.draw_text(
                (
                    x_index + 80,
                    y_item,
                    x_index + 180,
                    y_next - 10,
                ),
                f"{relic_set[i].num} 件套",
                fontname=fontname,
                max_fontsize=32,
                fill=WHITE,
            )
            if relic_set[i].properties:
                set_prop_icon = relic_set[i].properties[0].icon
                set_prop_value = relic_set[i].properties[0].display
                set_prop_image = await get_image(set_prop_icon)
                if set_prop_image:
                    set_prop_image = set_prop_image.resize((40, 40))
                    image_res.paste(
                        set_prop_image,
                        (x_index + 200, y_item + 15),
                        alpha=True,
                    )
                    image_res.draw_text(
                        (
                            x_index + 240,
                            y_item,
                            x_index + 320,
                            y_next - 10,
                        ),
                        set_prop_value,
                        fontname=fontname,
                        max_fontsize=24,
                        fill=WHITE,
                    )
            else:
                image_res.draw_text(
                    (
                        x_index + 200,
                        y_item,
                        x_index + 320,
                        y_next - 10,
                    ),
                    "--",
                    fontname=fontname,
                    max_fontsize=32,
                    fill=WHITE,
                )
        else:
            image_res.draw_text(
                (
                    x_index + 20,
                    y_item,
                    x_index + 320,
                    y_next - 10,
                ),
                "未激活套装",
                fontname=fontname,
                max_fontsize=32,
                fill=WHITE,
            )
    # relic score
    x_index += 355
    y_index = 1260
    image_res.draw_rounded_rectangle(
        (x_index, y_index, x_index + 240, y_index + 230),
        radius=15,
        outline=GRAY,
        width=2,
    )
    image_res.draw_text(
        (x_index + 30, y_index + 20, x_index + 210, y_index + 125),
        f"{relic_score_all}/10" if not relic_score_all.startswith("0") else "--",
        fontname=fontname,
        max_fontsize=64,
        fill=WHITE,
    )
    image_res.draw_text(
        (x_index + 30, y_index + 125, x_index + 210, y_index + 210),
        "SRS-N 评分",
        fontname=fontname,
        max_fontsize=36,
        fill=WHITE,
    )
    image_res.draw_text(
        (80, 1550, 1640, 1600),
        f"Created by Mar-7th/March7th. Panel data provided by MiHoMo API. Updated at {time}",
        fontname=fontname,
        max_fontsize=36,
        fill=WHITE,
    )
    return image_res.save_png()
