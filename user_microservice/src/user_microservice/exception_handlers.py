from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from user_microservice.business_errors import (
    EmptyUpdateFieldsError,
    InvalidCredentialsError,
    TokenInvalidError,
    TokenNotFoundError,
    TokenTypeMismatchError,
    UserDeactivatedError,
    UserNotFoundError,
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


def _unique_violation_detail(exc: IntegrityError) -> str:
    message = str(exc.orig).lower() if exc.orig is not None else str(exc).lower()
    if "email" in message:
        return "User with this email already exists"
    return "Resource already exists"


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
        return _error_response(request, 409, _unique_violation_detail(exc), reason="DB: unique constraint violation")
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
    TokenInvalidError: (401, "Could not validate credentials", _AUTH_HEADER, "Security: Invalid or Expired JWT token provided"),
    TokenTypeMismatchError: (401, "Invalid token type", _AUTH_HEADER, "Security: Token type mismatch attempt"),
    TokenNotFoundError: (401, "Session has expired. Please Log In again", None, "Security: Refresh token not found in Redis"),
    UserDeactivatedError: (403, "User account is deactivated", None, "Auth: Attempt to access via deactivated user"),
    InvalidCredentialsError: (401, "Invalid email or password", None, "Auth: Failed Log In attempt (Wrong credentials)"),
    EmptyUpdateFieldsError: (400, "No fields provided for update", None, "User: Update request without fields"),
    UserNotFoundError: (404, "User not found", None, "User: Requested user profile not found"),
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
