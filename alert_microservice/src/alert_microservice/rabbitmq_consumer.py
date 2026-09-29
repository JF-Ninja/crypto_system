import json

import httpx
from aio_pika import Message
from fastapi import HTTPException

from alert_microservice.interfaces import AbstractRedisClass, AbstractAlertClass
from alert_microservice.logger import logger
from alert_microservice.smtplib_sender import email_sender


class RabbitMQConsumer:
    def __init__(self, redis: AbstractRedisClass, crypto_q, trigger_q, trigger_ex, alert_repo: AbstractAlertClass):
        self.redis = redis
        self.crypto_q = crypto_q
        self.trigger_q = trigger_q
        self.trigger_ex = trigger_ex
        self.alert_repo = alert_repo

    async def monitoring_alerts(self):
        try:
            async with self.crypto_q.iterator() as q:
                async for message in q:
                    async with message.process():
                        try:
                            actual_message = json.loads(message.body.decode('utf-8'))
                            hash_key_greater = f"alerts:{actual_message['symbol']}:greater_than"
                            hash_key_less = f"alerts:{actual_message['symbol']}:less_than"
                            price = float(actual_message["price"])
                            actual_alerts_greater = await self.redis.get_hash_pairs(hash_key_greater)
                            actual_alerts_less = await self.redis.get_hash_pairs(hash_key_less)
                            for key, value in actual_alerts_greater.items():
                                if price >= float(value):
                                    await self.redis.delete_hash_pairs(hash_key_greater, key)
                                    alert = {"alert_id": int(key)}
                                    msg = Message(json.dumps(alert).encode('utf-8'))
                                    await self.trigger_ex.publish(msg, routing_key="")
                            for key, value in actual_alerts_less.items():
                                if price <= float(value):
                                    await self.redis.delete_hash_pairs(hash_key_less, key)
                                    alert = {"alert_id": int(key)}
                                    msg = Message(json.dumps(alert).encode('utf-8'))
                                    await self.trigger_ex.publish(msg, routing_key="")

                        except Exception as inner_e:
                            logger.exception(f"Error processing a single message: {repr(inner_e)}")
        except Exception as e:
            logger.exception(f"Critical listener error: {repr(e)}")

    async def activating_alerts(self):
        try:
            async with self.trigger_q.iterator() as q:
                async for message in q:
                    async with message.process():
                        try:
                            actual_message = json.loads(message.body.decode('utf-8'))
                            logger.info(actual_message)
                            alert_id = actual_message["alert_id"]
                            actual_alert = await self.alert_repo.find_one_or_none(id=alert_id, is_triggered=False)
                            if actual_alert:
                                await self.alert_repo.update(filter_by={"id":alert_id}, values={"is_triggered": True})
                                async with httpx.AsyncClient() as client:
                                    try:
                                        response = await client.post("http://users-app:8000/internal/users/get_user", params={"user_id": actual_alert.user_id})
                                    except httpx.RequestError:
                                        raise HTTPException(status_code=503, detail="User service is unavailable")
                                user_info = response.json()
                                logger.info(f"FULL USER INFO: {user_info}")
                                user_email = user_info.get("email")
                                logger.info(user_email)
                                await email_sender(user_email, actual_alert.ticker_name, actual_alert.target_price)
                                await self.alert_repo.save_changes()
                        except Exception as inner_e:
                            logger.exception(f"Error processing a single message: {repr(inner_e)}")
        except Exception as e:
            logger.exception(f"Critical listener error: {repr(e)}")
