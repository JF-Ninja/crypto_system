import httpx
from fastapi import Request

from alert_microservice.business_errors import ExternalServiceUnavailableError, TokenInvalidError
from alert_microservice.interfaces import AbstractExternalClient


class MicroserviceClient(AbstractExternalClient):
    def __init__(self, request: Request, timeout: float = 5.0):
        self.request = request
        self.timeout = httpx.Timeout(timeout)
        self.request_id = getattr(request.state, "request_id", "unknown")

    async def send_request(self, method: str, url: str, **kwargs) -> dict:
        headers = kwargs.pop("headers", {})
        headers.update({"X-Request-ID": self.request_id,"Content-Type": "application/json"})
        service_name = url.split("//")[-1].split("/")[0]
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(method, url, headers=headers, **kwargs)
                if response.status_code == 401:
                    self.request.state.log_reason = f"Security: Auth failed at {service_name} (Token invalid/expired)"
                    raise TokenInvalidError()
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                self.request.state.log_reason = f"Integration: {service_name} responded with error status {status}"
                raise ExternalServiceUnavailableError() from exc
            except httpx.RequestError as exc:
                self.request.state.log_reason = f"Integration: {service_name} is physically dead or timeout reached"
                raise ExternalServiceUnavailableError() from exc