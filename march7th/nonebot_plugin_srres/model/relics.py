from typing import Literal

from pydantic import BaseModel

from .common import Property


class RelicType(BaseModel):
    id: str
    set_id: str
    name: str
    rarity: int
    type: Literal["HEAD", "HAND", "BODY", "FOOT", "NECK", "OBJECT"]
    max_level: int
    main_affix_id: str
    sub_affix_id: str
    icon: str


class RelicSetType(BaseModel):
    id: str
    name: str
    properties: list[list[Property]]
    desc: list[str]
    icon: str
    guide_overview: list[str]


class AffixType(BaseModel):
    affix_id: str
    property: str
    base: float
    step: float
    step_num: int = 0


class RelicMainAffixType(BaseModel):
    id: str
    affixes: dict[str, AffixType]


class RelicSubAffixType(BaseModel):
    id: str
    affixes: dict[str, AffixType]


RelicIndex = dict[str, RelicType]
RelicSetIndex = dict[str, RelicSetType]
RelicMainAffixIndex = dict[str, RelicMainAffixType]
RelicSubAffixIndex = dict[str, RelicSubAffixType]
