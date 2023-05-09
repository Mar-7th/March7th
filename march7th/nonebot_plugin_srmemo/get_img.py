from io import BytesIO
from typing import Optional

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

fontname = "HYRunYuan-65W"


def time_fmt(sec: int) -> str:
    min, _ = divmod(int(sec), 60)
    hour, min = divmod(min, 60)
    return f"{hour}小时{min}分"


# def get_icon(id: str) -> Optional[Image.Image]:
#     icon = srres.get_icon(id=id)
#     if icon:
#         return Image.open(icon).convert("RGBA")
#     return None


async def get_srmemo_img(sr_uid, sr_basic_info, sr_note) -> Optional[BytesIO]:
    nickname = sr_basic_info["nickname"]  # 昵称
    level = sr_basic_info["level"]  # 等级

    # 开拓力
    stamina = sr_note["current_stamina"]
    max_stamina = sr_note["max_stamina"]
    stamina_str = f"{stamina}/{max_stamina}"
    stamina_recovery_time = time_fmt(sr_note["stamina_recover_time"])

    # 派遣列表
    expeditions = []
    for i in range(4):
        if i < len(sr_note["expeditions"]):
            expedition = sr_note["expeditions"][i]
            expeditions.append(expedition)

    # 绘制图片
    image_bg = BuildImage.new("RGBA", (800, 260), BACKGROUND)

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

    # 开拓力
    image_bg.draw_text(
        (50, 190, 180, 220), "开拓力", max_fontsize=24, fontname=fontname, fill=GRAY2
    )
    image_bg.draw_text(
        (200, 170, 480, 230),
        stamina_str,
        max_fontsize=54,
        fontname=fontname,
        fill=GRAY3,
    )
    if stamina == max_stamina:
        image_bg.draw_text(
            (500, 190, 720, 220),
            "已回满",
            max_fontsize=24,
            fontname=fontname,
            fill=GRAY2,
        )
    else:
        image_bg.draw_text(
            (500, 190, 720, 220),
            f"{stamina_recovery_time} 后回满",
            max_fontsize=24,
            fontname=fontname,
            fill=GRAY2,
        )

    image_bg.draw_line((50, 250, 750, 250), fill=GRAY1, width=2)

    # 派遣列表
    lines = []
    for expedition in expeditions:
        name = expedition["name"]
        remaining_time: str = time_fmt(expedition["remaining_time"])
        line = BuildImage.new("RGBA", (800, 60), BACKGROUND)
        line.draw_rounded_rectangle((50, 0, 750, 60), radius=10, outline=GRAY1, width=2)
        line.draw_text(
            (60, 0, 400, 60), name, max_fontsize=24, fontname=fontname, fill=GRAY3
        )
        if int(expedition["remaining_time"]) == 0:
            line.draw_text(
                (400, 0, 700, 60),
                f"已完成",
                max_fontsize=24,
                fontname=fontname,
                fill=GRAY3,
            )
        else:
            line.draw_text(
                (400, 0, 700, 60),
                f"剩余 {remaining_time}",
                max_fontsize=24,
                fontname=fontname,
                fill=GRAY3,
            )
        lines.append(line)

    # 绘制总图
    height = 300 + len(lines) * 80
    image_res = BuildImage.new("RGBA", (800, height), BACKGROUND)
    image_res.paste(image_bg, (0, 0))

    y_index = 280
    for line in lines:
        image_res.paste(line, (0, y_index), alpha=True)
        y_index += 80

    image_res.draw_rectangle((10, 10, 800 - 10, height - 10), outline=GRAY3, width=6)
    image_res.draw_rectangle((20, 20, 800 - 20, height - 20), outline=GRAY2, width=2)

    return image_res.save_png()


async def get_srmonth_img(sr_uid, sr_basic_info, sr_month) -> Optional[BytesIO]:
    nickname = sr_basic_info["nickname"]  # 昵称
    level = sr_basic_info["level"]  # 等级

    day_hcoin = sr_month["day_data"]["current_hcoin"]
    day_rails_pass = sr_month["day_data"]["current_rails_pass"]
    last_day_hcoin = 0
    last_day_rails_pass = 0
    if int(sr_uid[0]) < 6:
        last_day_hcoin = sr_month["day_data"]["last_hcoin"]
        last_day_rails_pass = sr_month["day_data"]["last_rails_pass"]
    month_hcoin = sr_month["month_data"]["current_hcoin"]
    month_rails_pass = sr_month["month_data"]["current_rails_pass"]
    last_month_hcoin = sr_month["month_data"]["last_hcoin"]
    last_month_rails_pass = sr_month["month_data"]["last_rails_pass"]

    month_datas = [
        {
            "hcoin": day_hcoin,
            "pass": day_rails_pass,
        },
        {
            "hcoin": last_day_hcoin,
            "pass": last_day_rails_pass,
        },
        {
            "hcoin": month_hcoin,
            "pass": month_rails_pass,
        },
        {
            "hcoin": last_month_hcoin,
            "pass": last_month_rails_pass,
        },
    ]

    group_by = ""
    for i in sr_month["month_data"]["group_by"]:
        group_by += f"{i['action_name']}：{i['num']}（{i['percent']}%）\n"

    # 绘制图片
    image_bg = BuildImage.new("RGBA", (800, 800), BACKGROUND)
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
        (50, 190, 160, 220), "本日获取", max_fontsize=24, fontname=fontname, fill=GRAY2
    )
    image_bg.draw_text(
        (50, 260, 160, 290), "昨日获取", max_fontsize=24, fontname=fontname, fill=GRAY2
    )
    image_bg.draw_text(
        (50, 330, 160, 360), "本月获取", max_fontsize=24, fontname=fontname, fill=GRAY2
    )
    image_bg.draw_text(
        (50, 400, 160, 430), "上月获取", max_fontsize=24, fontname=fontname, fill=GRAY2
    )

    y_index = 170

    for data in month_datas:
        image_bg.draw_text(
            (200, y_index, 350, y_index + 60),
            str(data["hcoin"]),
            max_fontsize=48,
            fontname=fontname,
            fill=GRAY3,
        )
        image_bg.draw_text(
            (350, y_index + 20, 450, y_index + 40),
            "星琼",
            max_fontsize=24,
            fontname=fontname,
            fill=GRAY2,
        )
        image_bg.draw_text(
            (450, y_index, 550, y_index + 60),
            str(data["pass"]),
            max_fontsize=48,
            fontname=fontname,
            fill=GRAY3,
        )
        image_bg.draw_text(
            (550, y_index + 20, 750, y_index + 40),
            "星轨通票&星轨专票",
            max_fontsize=24,
            fontname=fontname,
            fill=GRAY2,
        )
        y_index = y_index + 70

    image_bg.draw_line((50, 450, 750, 450), fill=GRAY1, width=2)

    y_index = 480
    for line in group_by.split("\n"):
        image_bg.draw_text(
            (60, y_index), line, fontsize=24, fontname=fontname, fill=GRAY2
        )
        y_index = y_index + 40

    image_bg.draw_text(
        (500, 520, 720, 620), "开 拓", max_fontsize=100, fontname=fontname, fill=GRAY2
    )
    image_bg.draw_text(
        (500, 620, 720, 720), "月 历", max_fontsize=100, fontname=fontname, fill=GRAY2
    )
    image_bg.draw_rounded_rectangle(
        (480, 500, 740, 740), outline=GRAY2, width=2, radius=20
    )
    image_bg.draw_line((600, 620, 620, 620), fill=GRAY2)
    image_bg.draw_line((610, 610, 610, 630), fill=GRAY2)

    image_bg.draw_rectangle((10, 10, 800 - 10, 800 - 10), outline=GRAY3, width=6)
    image_bg.draw_rectangle((20, 20, 800 - 20, 800 - 20), outline=GRAY2, width=2)

    return image_bg.save_png()
