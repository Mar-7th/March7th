from pydantic import BaseModel


class PropertyType(BaseModel):
    type: str  # property type
    name: str  # property name
    field: str  # property field for affix
    affix: bool  # is relic or light cone affix
    ratio: bool  # is added ratio
    percent: bool  # is percent
    order: int  # property order
    icon: str  # property icon path


PropertyIndex = dict[str, PropertyType]
