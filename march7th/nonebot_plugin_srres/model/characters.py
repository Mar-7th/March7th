from pydantic import BaseModel

from .common import Property, Quantity, Promotion


class CharacterEvaluationType(BaseModel):
    image: str
    link: str


class CharacterType(BaseModel):
    id: str
    name: str
    tag: str
    rarity: int
    path: str
    element: str
    max_sp: float
    ranks: list[str]
    skills: list[str]
    skill_trees: list[str]
    icon: str
    preview: str
    portrait: str
    guide_overview: list[str] = []


class CharacterRankType(BaseModel):
    id: str
    rank: int
    desc: str
    materials: list[Quantity]
    level_up_skills: list[Quantity]
    icon: str


class CharacterSkillType(BaseModel):
    id: str
    name: str
    max_level: int
    element: str
    type: str
    type_text: str
    effect: str
    effect_text: str
    simple_desc: str
    desc: str
    params: list[list[float]]
    icon: str


class SkillTreeLevelType(BaseModel):
    promotion: int
    properties: list[Property]
    materials: list[Quantity]


class CharacterSkillTreeType(BaseModel):
    id: str
    max_level: int
    anchor: str
    pre_points: list[str]
    level_up_skills: list[Quantity]
    levels: list[SkillTreeLevelType]
    icon: str


class CharacterPromotionType(BaseModel):
    id: str
    values: list[dict[str, Promotion]]
    materials: list[list[Quantity]]


CharacterIndex = dict[str, CharacterType]
CharacterRankIndex = dict[str, CharacterRankType]
CharacterSkillIndex = dict[str, CharacterSkillType]
CharacterSkillTreeIndex = dict[str, CharacterSkillTreeType]
CharacterPromotionIndex = dict[str, CharacterPromotionType]
