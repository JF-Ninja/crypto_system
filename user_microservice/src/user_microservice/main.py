from fastapi import FastAPI
from user_microservice.api.user_api import external_router as user_external_router
from user_microservice.api.user_api import internal_router  as user_internal_router
from user_microservice.api.auth_api import internal_router  as auth_internal_router
from user_microservice.api.auth_api import external_router  as auth_external_router

app = FastAPI(root_path="/api/v1/users")

app.include_router(user_external_router)
app.include_router(user_internal_router)
app.include_router(auth_internal_router)
app.include_router(auth_external_router)