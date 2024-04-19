from pydantic import BaseModel


class DescriptionType(BaseModel):
    id: str  # description id
    title: str  # description title
    desc: str  # description desc


DescriptionIndex = dict[str, DescriptionType]
