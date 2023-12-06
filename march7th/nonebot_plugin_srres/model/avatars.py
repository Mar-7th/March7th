from typing import Dict

from pydantic import BaseModel


class AvatarType(BaseModel):
    id: str  # avartar id
    name: str  # avartar name
    icon: str  # avartar icon


AvatarIndex = Dict[str, AvatarType]
