from typing import Dict

from pydantic import BaseModel


class DescriptionType(BaseModel):
    id: str  # description id
    title: str  # description title
    desc: str  # description desc


DescriptionIndex = Dict[str, DescriptionType]
