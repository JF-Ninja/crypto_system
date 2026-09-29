import json

import httpx
from fastapi import HTTPException

from alert_microservice.interfaces import AbstractAlertClass, AbstractRedisClass
from alert_microservice.logger import logger
from alert_microservice.schema.alert_schema import SAlertBase


class AlertService:
    def __init__(self, repository: AbstractAlertClass, redis_repository: AbstractRedisClass):
        self.repository = repository
        self.redis = redis_repository


    async def create_alert(self, alert: SAlertBase, user_info: dict):

        alert_data = alert.model_dump()
        ticker = alert_data["ticker_name"]
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post("http://assets-app:8000/internal/assets/get_asset",json={"ticker_name": ticker})
            except httpx.RequestError:
                raise HTTPException(status_code=503, detail="Assets service is unavailable")
        asset_data = response.json()
        if asset_data.get(ticker) is None:
            raise HTTPException(status_code=404, detail="Assets nof found")

        asset_value = float(asset_data.get(ticker))
        if asset_value > alert_data["target_price"]:
            alert_data["trigger_type"] = "less_than"
        elif asset_value < alert_data["target_price"]:
            alert_data["trigger_type"] = "greater_than"
        else:
            raise HTTPException(status_code=400, detail="Asset already current price")


        alert_data["user_id"] = user_info["id"]
        existing_alert = await self.repository.find_all(user_id=alert_data["user_id"],
                                                        ticker_name=ticker,
                                                        target_price=alert_data["target_price"],
                                                        is_triggered=False)
        if existing_alert:
            raise HTTPException(status_code=409, detail="Alert for this ticker and price already created")

        result = await self.repository.add(alert_data)
        hash_key = f"alerts:{ticker}:{alert_data["trigger_type"]}"
        await self.redis.set_hash_pairs(hash_key, **{str(result.id): alert_data["target_price"]})
        await self.repository.save_changes()
        return result

    async def get_all_alerts(self, user_info: dict):
        return await self.repository.find_all(user_id=user_info["id"])