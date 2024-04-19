from io import BytesIO
from typing import Any, Optional

from pil_utils import BuildImage, text2image

try:
    from march7th.nonebot_plugin_srres import srres
except ModuleNotFoundError:
    from nonebot_plugin_srres import srres

BACKGROUND = (248, 248, 248)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

fontname = srres.get_font()
font_args = {
    "fontname": fontname,
    "fill": BLACK,
}


async def get_srhelp_img(plugin_info: dict[str, dict[str, str]]) -> Optional[BytesIO]:
    if not plugin_info:
        return None
    title = "March7th Help Menu"
    tip = "* [] 表示需要填入的参数，补充参数后无需带 []"
    git_repo = "github.com/Mar-7th/March7th"
    cols_height: list[int] = [0, 0]
    item_image_dict: dict[str, dict[str, Any]] = {}
    for k, v in plugin_info.items():
        description = v.get("description", "")
        usage = v.get("srhelp", "暂无帮助信息")
        item_text_image = text2image(
            f"[size=30][b]{k}[/b][/size]\n[size=20][i]{description}[/i][/size]\n[size=10] [/size]\n{usage}",
            fontsize=24,
            bg_color=BACKGROUND,
            **font_args,
        )
        item_image = BuildImage.new(
            "RGBA", (500, item_text_image.height + 40), BACKGROUND
        )
        item_image.paste(item_text_image, (20, 20))
        item_image.draw_rounded_rectangle(
            (10, 10, 490, item_image.height - 5), radius=10, outline=BLACK, width=2
        )
        pos_x = 30 + cols_height.index(min(cols_height)) * 500
        pos_y = 120 + cols_height[cols_height.index(min(cols_height))]
        cols_height[cols_height.index(min(cols_height))] += item_text_image.height + 40
        item_image_dict[k] = {}
        item_image_dict[k]["x"] = pos_x
        item_image_dict[k]["y"] = pos_y
        item_image_dict[k]["image"] = item_image
    if cols_height[0] < cols_height[1]:
        for k in item_image_dict.keys():
            item_image_dict[k]["x"] = (30 + 530) - item_image_dict[k]["x"]
    image = BuildImage.new("RGBA", (1060, 180 + max(cols_height)), BACKGROUND)
    image.draw_text((60, 30), title, fontsize=56, weight="bold", **font_args)
    image.draw_text(
        (700, image.height - 60), tip, fontsize=16, weight="bold", **font_args
    )
    image.draw_text(
        (700, image.height - 30), git_repo, fontsize=20, weight="bold", **font_args
    )
    for k, v in item_image_dict.items():
        image.paste(v["image"], (v["x"], v["y"]))
    return image.save_png()
