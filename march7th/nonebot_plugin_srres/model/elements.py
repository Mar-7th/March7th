from pydantic import BaseModel


class ElementType(BaseModel):
    id: str  # element id
    name: str  # element name
    desc: str  # element description
    color: str  # element color
    icon: str  # element icon path


ElementIndex = dict[str, ElementType]
