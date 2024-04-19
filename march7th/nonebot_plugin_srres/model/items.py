from pydantic import BaseModel


class ItemType(BaseModel):
    id: str  # item id
    name: str  # item name
    type: str  # item type
    sub_type: str  # item sub type
    rarity: int  # item rarity
    icon: str  # item icon path
    come_from: list[str]  # item come from


ItemIndex = dict[str, ItemType]
