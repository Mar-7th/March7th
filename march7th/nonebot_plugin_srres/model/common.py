from pydantic import BaseModel


class Quantity(BaseModel):
    id: str
    num: int


class Property(BaseModel):
    type: str
    value: float


class Promotion(BaseModel):
    base: float
    step: float
