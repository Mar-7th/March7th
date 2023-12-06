from typing import Dict, List, Literal

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
    properties: List[List[Property]]
    desc: List[str]
    icon: str
    guide_overview: List[str]


class AffixType(BaseModel):
    affix_id: str
    property: str
    base: float
    step: float
    step_num: int = 0


class RelicMainAffixType(BaseModel):
    id: str
    affixes: Dict[str, AffixType]


class RelicSubAffixType(BaseModel):
    id: str
    affixes: Dict[str, AffixType]


RelicIndex = Dict[str, RelicType]
RelicSetIndex = Dict[str, RelicSetType]
RelicMainAffixIndex = Dict[str, RelicMainAffixType]
RelicSubAffixIndex = Dict[str, RelicSubAffixType]
