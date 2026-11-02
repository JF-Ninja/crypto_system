import json

from websockets.exceptions import ConnectionClosed, ConnectionClosedError, ConnectionClosedOK
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from asset_microservice.business_errors import AssetExistsError, AssetNotFoundError, ExternalServiceUnavailableError


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


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return _error_response(
        request,
        500,
        "Internal server error",
        reason=f"Unhandled: {type(exc).__name__}",
    )


BUSINESS_ERRORS: dict[type[Exception], tuple[int, str, dict[str, str] | None, str]] = {
    AssetExistsError: (409, "Asset already exists", None, "Asset: Such asset already exists"),
    AssetNotFoundError: (404, "Asset not found", None, "Asset: Such asset not exists"),
    ExternalServiceUnavailableError: (
        503,
        "External service is temporarily unavailable",
        None,
        "Integration: exchange API communication failure",
    ),
}

WEBSOCKET_ERRORS = {
    ConnectionClosed: (True, "Network: WebSocket connection closed by remote server. Reconnecting..."),
    ConnectionClosedError: (True, "Network: WebSocket connection dropped with error. Reconnecting..."),
    ConnectionClosedOK: (True, "Network: WebSocket connection closed gracefully. Restarting..."),
    OSError: (True, "Network: Physical network error or DNS resolution failure. Reconnecting..."),
    json.JSONDecodeError: (False, "Validation: Received invalid JSON from exchange stream"),
    KeyError: (False, "Validation: Missing expected key ('s' or 'p') in stream message"),
    ValueError: (False, "Validation: Data type casting error inside stream message processing"),
}


def match_websocket_error(exc: BaseException) -> tuple[bool, str] | None:
    for cls in type(exc).__mro__:
        if cls in WEBSOCKET_ERRORS:
            return WEBSOCKET_ERRORS[cls]
    return None


def _make_business_handler(status_code: int, detail: str, headers: dict[str, str] | None, reason: str):
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(request, status_code, detail, reason=reason, headers=headers)

    return handler


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    for exc_class, (status_code, detail, headers, reason) in BUSINESS_ERRORS.items():
        app.add_exception_handler(exc_class, _make_business_handler(status_code, detail, headers, reason))
