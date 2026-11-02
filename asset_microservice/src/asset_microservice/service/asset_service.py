import asyncio
import json
from typing import List

import httpx
from aio_pika import Message
from websockets import connect

from asset_microservice.logger import logger
from asset_microservice.business_errors import AssetExistsError, AssetNotFoundError, ExternalServiceUnavailableError
from asset_microservice.exception_handlers import match_websocket_error
from asset_microservice.interface import AbstractAssetRepository
from asset_microservice.schema.asset_schema import SAssetCreate, SAssetName
from asset_microservice.config import ticker_config


class AssetService:

    def __init__(self, repository: AbstractAssetRepository):
        self.repository = repository
        self.hash_key = "crypto:tickers"

    async def create_asset(self, asset: List[SAssetCreate]):
        assets_dict = {}
        created_results = []
        for name in asset:
            ticker = name.ticker_name
            old_asset = await self.repository.get_hash_pairs(self.hash_key, ticker)
            if old_asset.get(ticker) is not None:
                raise AssetExistsError()
            assets_dict[ticker] = 0
            created_results.append({"ticker": ticker})
        await self.repository.set_hash_pairs(self.hash_key, **assets_dict)
        return created_results


    async def get_assets(self, asset: SAssetName | None = None):
        if asset is None:
            return await self.repository.get_hash_pairs(self.hash_key)
        return await self.repository.get_hash_pairs(self.hash_key, asset.ticker_name)

    async def update_assets(self):
        url = "https://api1.binance.com/api/v3/ticker/price"
        new_dict = {}
        async with httpx.AsyncClient() as client:
            try:
                old_asset = await self.repository.get_hash_pairs(self.hash_key)
                resp = await client.get(url)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise ExternalServiceUnavailableError() from exc
            for ticker in resp.json():
                symbol = ticker.get("symbol")
                price = ticker.get("price")
                if symbol in old_asset.keys():
                    new_dict[symbol] = price
            new_dict = await self.repository.set_hash_pairs(self.hash_key, **new_dict)
        return new_dict

    async def delete_asset(self, asset: SAssetName):
        ticker = asset.ticker_name
        old_asset = await self.repository.get_hash_pairs(self.hash_key, ticker)
        if old_asset.get(ticker) is None:
            raise AssetNotFoundError()
        await self.repository.delete_hash_pairs(self.hash_key, ticker)
        return {"ticker": ticker}


    async def auto_update_asset(self, exchange):
        last_sent_prices = {}
        while True:
            try:
                str1 = ""
                assets = await self.repository.get_hash_pairs(self.hash_key)
                for asset in assets.keys():
                    str1 += "/" + asset.lower() + "@aggTrade"
                url = f"{ticker_config.url}{str1}"
                async with connect(url) as websocket:
                    async def check_actual_assets():
                        while True:
                            await asyncio.sleep(15)
                            actual_assets = await self.repository.get_hash_pairs(self.hash_key)
                            if assets.keys() != actual_assets.keys():
                                logger.info("Assets list changed in Redis. Closing websocket to resubscribe...")
                                await websocket.close()
                                break
                    task = asyncio.create_task(check_actual_assets())
                    try:
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                symbol = data["s"]
                                price = data["p"]
                                if last_sent_prices.get(symbol) == price:
                                    continue
                                if symbol in assets.keys():
                                    await self.repository.set_hash_pairs(self.hash_key, **{symbol: price})
                                    ticker = {"symbol": symbol, "price": price}
                                    last_sent_prices[symbol] = price
                                    msg = Message(json.dumps(ticker).encode('utf-8'))
                                    await exchange.publish(msg, routing_key="")
                            except Exception as data_e:
                                matched = match_websocket_error(data_e)
                                if matched is not None and not matched[0]:
                                    _, log_reason = matched
                                    logger.warning(f"{log_reason}. Error details: {repr(data_e)}")
                                else:
                                    raise data_e
                    finally:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
            except Exception as stream_e:
                matched = match_websocket_error(stream_e)
                if matched is not None:
                    _, log_reason = matched
                    logger.error(f"{log_reason}. System error: {repr(stream_e)}")
                else:
                    logger.exception(f"Unhandled critical exception in ticker producer: {repr(stream_e)}")
                await asyncio.sleep(5)