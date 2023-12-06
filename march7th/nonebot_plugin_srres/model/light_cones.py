from typing import Dict, List

from pydantic import BaseModel

from .common import Promotion, Property, Quantity


class LightConeType(BaseModel):
    id: str
    name: str
    rarity: int
    path: str
    icon: str
    preview: str
    portrait: str
    guide_overview: List[str] = []


class LightConeRankType(BaseModel):
    id: str
    skill: str
    desc: str
    params: List[List[float]]
    properties: List[List[Property]]


class LightConePromotionType(BaseModel):
    id: str
    values: List[Dict[str, Promotion]]
    materials: List[List[Quantity]]


LightConeIndex = Dict[str, LightConeType]
LightConeRankIndex = Dict[str, LightConeRankType]
LightConePromotionIndex = Dict[str, LightConePromotionType]
