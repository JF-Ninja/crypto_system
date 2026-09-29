from pydantic import BaseModel

class SAssetName(BaseModel):
    ticker_name: str

class SAssetCreate(SAssetName):
    current_price: float


class SAssetUpdate(SAssetName):
    current_price: float