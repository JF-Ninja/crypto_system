from fastapi import FastAPI

from alert_microservice.api.alert_api import router as alerts_router

def register_routers(app: FastAPI) -> None:
    app.include_router(alerts_router)