from alert_microservice.business_errors import AlertExistError, AssetCurrentPriceError, AssetNotFound
from alert_microservice.interfaces import AbstractAlertClass, AbstractRedisClass, AbstractExternalClient
from alert_microservice.schema.alert_schema import SAlertBase


class AlertService:
    def __init__(self, repository: AbstractAlertClass, redis_repository: AbstractRedisClass, client: AbstractExternalClient):
        self.repository = repository
        self.redis = redis_repository
        self.client = client

    async def create_alert(self, alert: SAlertBase, user_info: dict):

        alert_data = alert.model_dump()
        ticker = alert_data["ticker_name"]
        asset_data = await self.client.send_request(method="POST",url="http://assets-app:8000/internal/assets/get_asset",json={"ticker_name": ticker})

        if asset_data.get(ticker) is None:
            raise AssetNotFound()

        asset_value = float(asset_data.get(ticker))
        if asset_value > alert_data["target_price"]:
            alert_data["trigger_type"] = "less_than"
        elif asset_value < alert_data["target_price"]:
            alert_data["trigger_type"] = "greater_than"
        else:
            raise AssetCurrentPriceError()

        alert_data["user_id"] = user_info["id"]
        existing_alert = await self.repository.find_all(user_id=alert_data["user_id"], ticker_name=ticker,target_price=alert_data["target_price"],is_triggered=False)
        if existing_alert:
            raise AlertExistError()

        result = await self.repository.add(alert_data)
        hash_key = f"alerts:{ticker}:{alert_data["trigger_type"]}"
        await self.redis.set_hash_pairs(hash_key, **{str(result.id): alert_data["target_price"]})
        return result

    async def get_all_alerts(self, user_info: dict):
        return await self.repository.find_all(user_id=user_info["id"])