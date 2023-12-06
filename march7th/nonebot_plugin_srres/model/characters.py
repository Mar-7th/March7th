from typing import Dict, List

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
    ranks: List[str]
    skills: List[str]
    skill_trees: List[str]
    icon: str
    preview: str
    portrait: str
    guide_overview: List[str] = []
    guide_material: List[str] = []


class CharacterRankType(BaseModel):
    id: str
    rank: int
    desc: str
    materials: List[Quantity]
    level_up_skills: List[Quantity]
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
    params: List[List[float]]
    icon: str


class SkillTreeLevelType(BaseModel):
    promotion: int
    properties: List[Property]
    materials: List[Quantity]


class CharacterSkillTreeType(BaseModel):
    id: str
    max_level: int
    anchor: str
    pre_points: List[str]
    level_up_skills: List[Quantity]
    levels: List[SkillTreeLevelType]
    icon: str


class CharacterPromotionType(BaseModel):
    id: str
    values: List[Dict[str, Promotion]]
    materials: List[List[Quantity]]


CharacterIndex = Dict[str, CharacterType]
CharacterRankIndex = Dict[str, CharacterRankType]
CharacterSkillIndex = Dict[str, CharacterSkillType]
CharacterSkillTreeIndex = Dict[str, CharacterSkillTreeType]
CharacterPromotionIndex = Dict[str, CharacterPromotionType]
