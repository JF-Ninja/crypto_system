
from pydantic import BaseModel, Field


class SAlertBase(BaseModel):
    target_price: float = Field(ge=0, le=120000)
    ticker_name: str