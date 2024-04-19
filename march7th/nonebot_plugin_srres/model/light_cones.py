from pydantic import BaseModel

from .common import Property, Quantity, Promotion


class LightConeType(BaseModel):
    id: str
    name: str
    rarity: int
    path: str
    icon: str
    preview: str
    portrait: str
    guide_overview: list[str] = []


class LightConeRankType(BaseModel):
    id: str
    skill: str
    desc: str
    params: list[list[float]]
    properties: list[list[Property]]


class LightConePromotionType(BaseModel):
    id: str
    values: list[dict[str, Promotion]]
    materials: list[list[Quantity]]


LightConeIndex = dict[str, LightConeType]
LightConeRankIndex = dict[str, LightConeRankType]
LightConePromotionIndex = dict[str, LightConePromotionType]
