from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from alert_microservice.business_errors import (
    AlertExistError,
    AssetCurrentPriceError,
    AssetNotFound,
    ExternalServiceUnavailableError,
    TokenInvalidError,
)

UNIQUE_VIOLATION_SQLSTATE = "23505"

_AUTH_HEADER = {"WWW-Authenticate": "Bearer"}


def _error_response(
    request: Request,
    status_code: int,
    detail: str,
    *,
    reason: str,
    headers: dict[str, str] | None = None,
    **extra,
) -> JSONResponse:
    if not getattr(request.state, "log_reason", None):
        request.state.log_reason = reason
    body = {"detail": detail, **extra, "request_id": getattr(request.state, "request_id", "unknown")}
    return JSONResponse(status_code=status_code, content=body, headers=headers)


def _sqlstate(exc: IntegrityError) -> str | None:
    orig = exc.orig
    if orig is None:
        return None
    return getattr(orig, "sqlstate", None)


def _is_unique_violation(exc: IntegrityError) -> bool:
    return _sqlstate(exc) == UNIQUE_VIOLATION_SQLSTATE


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error_response(
        request,
        exc.status_code,
        exc.detail,
        reason=f"HTTP exception: {exc.detail}",
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    fields = ", ".join(".".join(str(part) for part in err["loc"]) for err in errors)
    return _error_response(
        request,
        422,
        "Validation error",
        reason=f"Validation error in: {fields}",
        errors=jsonable_encoder(errors),
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    if _is_unique_violation(exc):
        return _error_response(request, 409, "Resource already exists", reason="DB: unique constraint violation")
    return _error_response(
        request,
        400,
        "Invalid data",
        reason=f"DB: integrity error {type(exc.orig).__name__} (sqlstate={_sqlstate(exc)})",
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return _error_response(
        request,
        500,
        "Internal server error",
        reason=f"Unhandled: {type(exc).__name__}",
    )


BUSINESS_ERRORS: dict[type[Exception], tuple[int, str, dict[str, str] | None, str]] = {
    AlertExistError: (409, "Such alert already exists", None, "Alert: Alert for this user, asset, price already exists"),
    AssetCurrentPriceError: (400, "Asset already current price", None, "Asset: Alert's and Asset's prices are the same"),
    AssetNotFound: (404, "Asset not found", None, "Asset: Asset not found in assets_microservice"),
    TokenInvalidError: (401, "Could not validate credentials", _AUTH_HEADER, "Security: Invalid or Expired JWT token provided"),
    ExternalServiceUnavailableError: (503, "External service is temporarily unavailable", None, "Integration: microservice communication failure"),
}


def _make_business_handler(status_code: int, detail: str, headers: dict[str, str] | None, reason: str):
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(request, status_code, detail, reason=reason, headers=headers)

    return handler


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    for exc_class, (status_code, detail, headers, reason) in BUSINESS_ERRORS.items():
        app.add_exception_handler(exc_class, _make_business_handler(status_code, detail, headers, reason))
