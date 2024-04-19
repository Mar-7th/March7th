from pydantic import BaseModel


class PathType(BaseModel):
    id: str  # path id
    text: str  # path text
    name: str  # path name
    desc: str  # path description
    icon: str  # path icon path


PathIndex = dict[str, PathType]
