import asyncio
import json
from typing import List

import httpx
import websockets
from aio_pika import Message
from fastapi import HTTPException
from websockets import connect

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
                raise HTTPException(status_code=409, detail=f"Asset {ticker} already exists")
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
               old_asset = await self.repository.get_hash_pairs(self.hash_key)
               resp = await client.get(url)
               for ticker in resp.json():
                   symbol = ticker.get("symbol")
                   price = ticker.get("price")
                   if symbol in old_asset.keys():
                       new_dict[symbol] = price
               new_dict = await self.repository.set_hash_pairs(self.hash_key, **new_dict)
        return new_dict

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
                                await websocket.close()
                                break
                    task = asyncio.create_task(check_actual_assets())
                    try:
                        async for message in websocket:
                            data = json.loads(message)
                            symbol = data.get("s")
                            price = data.get("p")
                            if last_sent_prices.get(symbol) == price:
                                continue
                            else:
                                if symbol in assets.keys():
                                    await self.repository.set_hash_pairs(self.hash_key, **{symbol: price})
                                    ticker = {"symbol": symbol, "price": price}
                                    last_sent_prices[symbol] = price
                                    message = Message(json.dumps(ticker).encode('utf-8'))
                                    await exchange.publish(message, routing_key="")
                    finally:
                        task.cancel()
            except websockets.exceptions.ConnectionClosed as e:
                print(f"Connection closed: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Exception: {e}")
                await asyncio.sleep(5)



    async def delete_asset(self, asset: SAssetName):
        ticker = asset.ticker_name
        old_asset = await self.repository.get_hash_pairs(self.hash_key, ticker)
        if old_asset.get(ticker) is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        await self.repository.delete_hash_pairs(self.hash_key, ticker)
        return {"ticker": ticker}

