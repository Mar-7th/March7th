import math

try:
    from march7th.nonebot_plugin_srres import srres
except ModuleNotFoundError:
    from nonebot_plugin_srres import srres


def get_level_up_skills_from_character_rank(info):
    level_up_skills = []
    id = str(info["AvatarID"])
    rank = info["Rank"] if "Rank" in info else 0
    rank_list = srres.ResIndex["characters"][id]["ranks"][:rank]
    for rank_item in rank_list:
        level_up_skills += srres.ResIndex["character_ranks"][rank_item][
            "level_up_skills"
        ]
    return level_up_skills


def get_skill_info_by_level_up_skills(info, level_up_skills):
    skill_info = []
    id = str(info["AvatarID"])
    skill_list = srres.ResIndex["characters"][id]["skills"]
    for skill in skill_list:
        if not str(skill).endswith("6"):
            skill_info.append(
                {
                    "name": srres.ResIndex["character_skills"][skill]["name"],
                    "level": 0,
                    "icon": srres.ResIndex["character_skills"][skill]["icon"],
                }
            )
    for level_up_skill in level_up_skills:
        for i in range(len(skill_info)):
            if (
                skill_info[i]["name"]
                == srres.ResIndex["character_skills"][level_up_skill["id"]]["name"]
            ):
                if isinstance(level_up_skill["num"], int):
                    skill_info[i]["level"] = int(skill_info[i]["level"]) + int(
                        level_up_skill["num"]
                    )
                break
    return skill_info


def get_level_up_skills_from_character_skill_tree(info):
    level_up_skills = []
    skill_tree_list = info["BehaviorList"]
    for item in skill_tree_list:
        id = str(item["BehaviorID"])
        level = item["Level"]
        skill_list = srres.ResIndex["character_skill_trees"][id]["level_up_skills"]
        for skill in skill_list:
            skill["num"] *= level
            level_up_skills.append(skill)
    return level_up_skills


def get_properties_from_character_skill_tree(info):
    properties = []
    skill_tree_list = info["BehaviorList"]
    for item in skill_tree_list:
        id = str(item["BehaviorID"])
        level = item["Level"]
        skill_properties = srres.ResIndex["character_skill_trees"][id]["levels"][
            level - 1
        ]["properties"]
        for property in skill_properties:
            properties.append(property)
    return properties


def get_promotions_from_character(info):
    promotions = {}
    id = str(info["AvatarID"])
    level = info["Level"]
    promotion = info["Promotion"]
    values = srres.ResIndex["character_promotions"][id]["values"][promotion]
    for k, v in values.items():
        promotions[k] = v["base"] + v["step"] * (level - 1)
    return promotions


def parse_light_cone(info):
    light_cone_info = {}
    if "EquipmentID" in info:
        info = info["EquipmentID"]
        id = str(info["ID"])
        light_cone_info["name"] = srres.ResIndex["light_cones"][id]["name"]
        light_cone_info["rarity"] = srres.ResIndex["light_cones"][id]["rarity"]
        light_cone_info["rank"] = info["Rank"]
        light_cone_info["level"] = info["Level"]
        light_cone_info["icon"] = srres.ResIndex["light_cones"][id]["icon"]
    return light_cone_info


def get_properties_from_light_cone_rank(info):
    properties = []
    if "EquipmentID" in info:
        info = info["EquipmentID"]
        id = str(info["ID"])
        rank = info["Rank"]
        properties = srres.ResIndex["light_cone_ranks"][id]["properties"][rank - 1]
    return properties


def get_promotions_from_light_cone(info, promotions):
    if "EquipmentID" in info:
        info = info["EquipmentID"]
        id = str(info["ID"])
        level = info["Level"]
        promotion = info["Promotion"] if "Promotion" in info else 0
        values = srres.ResIndex["light_cone_promotions"][id]["values"][promotion]
        for k, v in values.items():
            promotions[k] += v["base"] + v["step"] * (level - 1)
    return promotions


def get_relic_info(info):
    relic_info = {}
    if "RelicList" in info:
        infos = info["RelicList"]
        for info in infos:
            id = str(info["ID"])
            type = str(info["Type"])
            level = info["Level"] if "Level" in info else 0
            relic_info[type] = {}
            relic_info[type]["name"] = srres.ResIndex["relics"][id]["name"]
            relic_info[type]["rarity"] = srres.ResIndex["relics"][id]["rarity"]
            main_affix_group = srres.ResIndex["relics"][id]["main_affix_id"]
            main_affix_id = str(info["MainAffixID"])
            main_affix = srres.ResIndex["relic_main_affixs"][main_affix_group][
                "affixs"
            ][main_affix_id]
            main_property = {
                "type": main_affix["property"],
                "value": main_affix["base"] + main_affix["step"] * level,
            }
            sub_affix_group = srres.ResIndex["relics"][id]["sub_affix_id"]
            sub_affixs = info["RelicSubAffix"] if "RelicSubAffix" in info else []
            sub_property = []
            for sub_affix in sub_affixs:
                sub_affix_id = str(sub_affix["SubAffixID"])
                cnt = sub_affix["Cnt"]
                step = sub_affix["Step"] if "Step" in sub_affix else 0
                sub_affix = srres.ResIndex["relic_sub_affixs"][sub_affix_group][
                    "affixs"
                ][sub_affix_id]
                sub_property.append(
                    {
                        "type": sub_affix["property"],
                        "value": sub_affix["base"] * cnt + sub_affix["step"] * step,
                    }
                )
            relic_info[type]["main_property"] = main_property
            relic_info[type]["sub_property"] = sub_property
            relic_info[type]["icon"] = srres.ResIndex["relics"][id]["icon"]
    return relic_info


def get_properties_from_relic_set(info):
    properties = []
    set_id_map = {}
    if "RelicList" in info:
        infos = info["RelicList"]
        for info in infos:
            id = str(info["ID"])
            set_id = srres.ResIndex["relics"][id]["set_id"]
            if set_id not in set_id_map:
                set_id_map[set_id] = 1
            else:
                set_id_map[set_id] += 1
    for k, v in set_id_map.items():
        if v >= 2:
            for i in srres.ResIndex["relic_sets"][k]["properties"][0]:
                properties.append(i)
        if v == 4:
            for i in srres.ResIndex["relic_sets"][k]["properties"][1]:
                properties.append(i)
    return properties


def parse_property(promotions, properties):
    property_dict = {}
    property_promotions = {}
    for property in properties:
        if property["type"] not in property_dict:
            property_dict[property["type"]] = property["value"]
        else:
            property_dict[property["type"]] += property["value"]
    for k, value in property_dict.items():
        field = srres.ResIndex["properties"][k]["field"]
        ratio = srres.ResIndex["properties"][k]["ratio"]
        order = srres.ResIndex["properties"][k]["order"]
        if field:
            if ratio and field in promotions:
                value = promotions[field] * value
            if field not in property_promotions:
                property_promotions[field] = {}
                property_promotions[field]["order"] = order
                property_promotions[field]["value"] = value
            else:
                if order < property_promotions[field]["order"]:
                    property_promotions[field]["order"] = order
                property_promotions[field]["value"] += value
    property_promotions = sorted(
        property_promotions.items(), key=lambda item: item[1]["order"]
    )
    property_promotions = {k: v["value"] for k, v in property_promotions}
    return property_promotions


def get_properties_from_relic_info(info):
    properties = []
    for v in info.values():
        properties.append(v["main_property"])
        properties += v["sub_property"]
    return properties


def get_relic_set_info(info):
    relic_set_info = []
    set_id_map = {}
    if "RelicList" in info:
        infos = info["RelicList"]
        for info in infos:
            id = str(info["ID"])
            set_id = srres.ResIndex["relics"][id]["set_id"]
            if set_id not in set_id_map:
                set_id_map[set_id] = 1
            else:
                set_id_map[set_id] += 1
    for k, v in set_id_map.items():
        icon = srres.ResIndex["relic_sets"][k]["icon"]
        if v >= 2:
            desc = "两件套"
            relic_set_info.append(
                {
                    "icon": icon,
                    "desc": desc,
                }
            )
        if v == 4:
            desc = "四件套"
            relic_set_info.append(
                {
                    "icon": icon,
                    "desc": desc,
                }
            )
    return relic_set_info


def get_character_rank_icons(info):
    icons = []
    id = str(info["AvatarID"])
    rank = info["Rank"] if "Rank" in info else 0
    rank_list = srres.ResIndex["characters"][id]["ranks"]
    rank_id = 1
    for rank_item in rank_list:
        icons.append(
            {
                "icon": srres.ResIndex["character_ranks"][rank_item]["icon"],
                "unlock": True if rank >= rank_id else False,
            }
        )
        rank_id = rank_id + 1
    return icons


def fix_relic_info(info):
    def parse_prop(prop):
        type = prop["type"]
        value = prop["value"]
        name = srres.ResIndex["properties"][type]["name"]
        # if "Ratio" in type or "Rate" in type or "Status" in type:
        if value < 1:
            value = format(math.floor(value * 1000) / 10.0, ".1f") + "%"
        else:
            value = str(math.floor(float(value)))
        return name, value

    for k, v in info.items():
        name, value = parse_prop(v["main_property"])
        info[k]["main_property"] = {
            "name": name,
            "value": value,
        }
        sub_property = []
        for vv in v["sub_property"]:
            name, value = parse_prop(vv)
            sub_property.append(
                {
                    "name": name,
                    "value": value,
                }
            )
        info[k]["sub_property"] = sub_property
    return info


def parse_display_list(info):
    info_new = []
    name_mapping = {}
    for v in srres.ResIndex["properties"].values():
        if v["field"] and v["field"] not in name_mapping:
            name_mapping[v["field"]] = v["name"]
    for k, v in info.items():
        if k in name_mapping:
            if k in {"hp", "atk", "def", "spd"}:
                value = str(math.floor(float(v)))
            else:
                value = format(math.floor(v * 1000) / 10.0, ".1f") + "%"
            info_new.append(
                {
                    "name": name_mapping[k],
                    "value": value,
                }
            )
    return info_new


def parse_character(info):
    character_info = {}
    id = str(info["AvatarID"])
    character_info["id"] = id
    character_info["name"] = srres.ResIndex["characters"][id]["name"]
    character_info["rarity"] = srres.ResIndex["characters"][id]["rarity"]
    character_info["level"] = info["Level"]
    character_info["rank"] = info["Rank"] if "Rank" in info else 0
    character_info["rank_icons"] = get_character_rank_icons(info)
    character_info["preview"] = srres.ResIndex["characters"][id]["preview"]
    character_info["path"] = srres.ResIndex["paths"][
        srres.ResIndex["characters"][id]["path"]
    ]["name"]
    character_info["path_icon"] = srres.ResIndex["paths"][
        srres.ResIndex["characters"][id]["path"]
    ]["icon"]
    character_info["element"] = srres.ResIndex["elements"][
        srres.ResIndex["characters"][id]["element"]
    ]["name"]
    character_info["element_icon"] = srres.ResIndex["elements"][
        srres.ResIndex["characters"][id]["element"]
    ]["icon"]
    character_info["color"] = srres.ResIndex["elements"][
        srres.ResIndex["characters"][id]["element"]
    ]["color"]
    level_up_skills = []
    level_up_skills += get_level_up_skills_from_character_rank(info)
    level_up_skills += get_level_up_skills_from_character_skill_tree(info)
    character_info["skill"] = get_skill_info_by_level_up_skills(info, level_up_skills)
    promotions = get_promotions_from_character(info)
    promotions = get_promotions_from_light_cone(info, promotions)
    character_info["light_cone"] = parse_light_cone(info)
    properties = []
    properties += get_properties_from_character_skill_tree(info)
    properties += get_properties_from_light_cone_rank(info)
    relic_info = get_relic_info(info)
    properties += get_properties_from_relic_info(relic_info)
    relic_info_new = fix_relic_info(relic_info)
    character_info["relic"] = relic_info_new
    character_info["relic_set"] = get_relic_set_info(info)
    properties += get_properties_from_relic_set(info)
    properties = parse_property(promotions, properties)
    character_info["promotion"] = parse_display_list(promotions)
    character_info["property"] = parse_display_list(properties)
    return character_info


def parse(response):
    result = {}
    result["player"] = {}
    player_info = response["PlayerDetailInfo"]
    result["player"]["uid"] = str(player_info["UID"])
    result["player"]["name"] = player_info["NickName"]
    result["player"]["level"] = player_info["Level"]
    result["player"]["head_icon"] = str(player_info["HeadIconID"])
    result["player"]["signature"] = (
        player_info["Signature"] if "Signature" in player_info else ""
    )
    character_list = []
    if "AssistAvatar" in player_info:
        character_list.append(player_info["AssistAvatar"])
    if "DisplayAvatarList" in player_info:
        for i in player_info["DisplayAvatarList"]:
            character_list.append(i)
    result["characters"] = []
    for i in character_list:
        result["characters"].append(parse_character(i))
    return result
