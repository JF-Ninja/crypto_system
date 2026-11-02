import base64
import json
import re
import time
import uuid

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from alert_microservice.logger import logger

_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _get_request_id(headers: dict[bytes, bytes]) -> str:
    incoming = headers.get(b"x-request-id", b"").decode("latin-1")
    if _VALID_REQUEST_ID.match(incoming):
        return incoming
    return uuid.uuid4().hex


def _get_user_id(headers: dict[bytes, bytes]) -> str:
    auth_header = headers.get(b"authorization", b"").decode("latin-1")
    if not auth_header.startswith("Bearer "):
        return "Anonymous"
    try:
        payload_b64 = auth_header.split(" ")[1].split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return str(payload["sub"])
    except Exception:
        return "malformed_token"


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        request_id = _get_request_id(headers)
        user_id = _get_user_id(headers)

        state = scope.setdefault("state", {})
        state["request_id"] = request_id
        state["user_id"] = user_id

        status_code = 500
        response_started = False
        unhandled: Exception | None = None

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                MutableHeaders(scope=message)["X-Request-ID"] = request_id
            await send(message)

        started_at = time.perf_counter()

        with logger.contextualize(request_id=request_id, user_id=user_id):
            try:
                await self.app(scope, receive, send_wrapper)
            except Exception as exc:
                unhandled = exc
                if response_started:
                    raise
                response = JSONResponse(status_code=500,content={"detail": "Internal server error", "request_id": request_id},)
                await response(scope, receive, send_wrapper)
            finally:
                self._log_request(scope, status_code, started_at, unhandled)

    @staticmethod
    def _log_request(scope: Scope, status_code: int, started_at: float, unhandled: Exception | None) -> None:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

        if unhandled is not None or status_code >= 500:
            level = "ERROR"
        elif status_code >= 400:
            level = "WARNING"
        else:
            level = "INFO"

        message = "{} {} -> {} ({} ms)"
        args = [scope["method"], scope["path"], status_code, duration_ms]
        reason = scope["state"].get("log_reason")
        if reason:
            message += " | {}"
            args.append(reason)

        log = logger.bind(method=scope["method"], url=scope["path"], status_code=status_code, duration_ms=duration_ms,)
        if unhandled is not None:
            log = log.opt(exception=unhandled)
        log.log(level, message, *args)

def register_middleware(app: FastAPI) -> None:
    app.add_middleware(RequestLoggingMiddleware)