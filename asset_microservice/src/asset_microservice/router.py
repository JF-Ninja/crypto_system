from fastapi import FastAPI

from asset_microservice.api.asset_api import external_router, internal_router

def register_routers(app: FastAPI) -> None:
    app.include_router(external_router)
    app.include_router(internal_router)