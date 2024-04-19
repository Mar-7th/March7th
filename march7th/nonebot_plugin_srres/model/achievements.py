from pydantic import BaseModel


class AchievementType(BaseModel):
    id: str  # achievement id
    series_id: str  # achievement series id
    title: str  # achievement title
    desc: str  # achievement description
    hide_desc: str  # achievement hide description
    hide: bool  # achievement hide


AchievementIndex = dict[str, AchievementType]
