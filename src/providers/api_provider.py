from __future__ import annotations

import os
from typing import Any

import requests

from src.domain.models import Brand, ModelYear, PriceResult, Reference, VehicleModel
from src.providers.base import FipeProvider

DEFAULT_BASE_URL = "https://fipe.parallelum.com.br/api/v2"
DEFAULT_TIMEOUT_SECONDS = 10.0
ALLOWED_VEHICLE_TYPES = frozenset({"cars", "motorcycles", "trucks"})


class FipeProviderError(Exception):
    """Base exception for provider failures."""


class FipeAuthError(FipeProviderError):
    """Raised when authentication is missing or invalid."""


class FipeSubscriptionError(FipeProviderError):
    """Raised when token exists but subscription does not allow the request."""


class FipeNotFoundError(FipeProviderError):
    """Raised when a requested resource does not exist."""


class FipeServerError(FipeProviderError):
    """Raised when FIPE API returns a server-side failure."""


class FipeRequestError(FipeProviderError):
    """Raised when a request fails for connectivity or payload reasons."""


class ApiProvider(FipeProvider):
    def __init__(
        self,
        token: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float | None = None,
        session: requests.Session | None = None,
    ) -> None:
        resolved_token = token or os.getenv("FIPE_TOKEN")
        if not resolved_token:
            raise FipeAuthError("FIPE_TOKEN is required to call FIPE API.")

        self.base_url = base_url.rstrip("/")
        self.timeout = self._resolve_timeout(timeout)
        self._token = resolved_token
        self._session = session or requests.Session()

    def list_references(self) -> list[Reference]:
        payload = self._request("references")
        return [Reference.from_dict(item) for item in self._ensure_list(payload)]

    def list_brands(self, vehicle_type: str, reference: str) -> list[Brand]:
        self._validate_vehicle_type(vehicle_type)
        payload = self._request(f"{vehicle_type}/brands", params={"reference": reference})
        return [Brand.from_dict(item) for item in self._ensure_list(payload)]

    def list_models(self, vehicle_type: str, brand_id: str, reference: str) -> list[VehicleModel]:
        self._validate_vehicle_type(vehicle_type)
        payload = self._request(
            f"{vehicle_type}/brands/{brand_id}/models",
            params={"reference": reference},
        )
        if isinstance(payload, dict):
            payload = payload.get("models", [])
        return [VehicleModel.from_dict(item) for item in self._ensure_list(payload)]

    def list_years(
        self,
        vehicle_type: str,
        brand_id: str,
        model_id: str,
        reference: str,
    ) -> list[ModelYear]:
        self._validate_vehicle_type(vehicle_type)
        payload = self._request(
            f"{vehicle_type}/brands/{brand_id}/models/{model_id}/years",
            params={"reference": reference},
        )
        return [ModelYear.from_dict(item) for item in self._ensure_list(payload)]

    def get_price(
        self,
        vehicle_type: str,
        brand_id: str,
        model_id: str,
        year_id: str,
        reference: str,
    ) -> PriceResult:
        self._validate_vehicle_type(vehicle_type)
        payload = self._request(
            f"{vehicle_type}/brands/{brand_id}/models/{model_id}/years/{year_id}",
            params={"reference": reference},
        )
        if not isinstance(payload, dict):
            raise FipeRequestError("Invalid response format for price endpoint.")
        return PriceResult.from_dict(payload)

    def _request(self, path: str, params: dict[str, str] | None = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {"X-Subscription-Token": self._token}

        try:
            response = self._session.request(
                method="GET",
                url=url,
                headers=headers,
                params=params,
                timeout=self.timeout,
            )
        except requests.Timeout as error:
            raise FipeRequestError("Request timeout while calling FIPE API.") from error
        except requests.RequestException as error:
            raise FipeRequestError("Request failure while calling FIPE API.") from error

        error_message = self._extract_error_message(response)
        error_suffix = f" Details: {error_message}" if error_message else ""
        if response.status_code == 404:
            raise FipeNotFoundError(f"Resource not found: {path}.{error_suffix}")
        if response.status_code == 401:
            raise FipeAuthError(
                f"FIPE API authentication failed. Check your FIPE_TOKEN.{error_suffix}"
            )
        if response.status_code == 402:
            raise FipeSubscriptionError(
                "FIPE API subscription does not allow this request (402). "
                f"Check token plan/credits on FipeOnline.{error_suffix}"
            )
        if response.status_code >= 500:
            raise FipeServerError(
                f"Server error from FIPE API ({response.status_code}).{error_suffix}"
            )
        if response.status_code >= 400:
            raise FipeRequestError(
                f"FIPE API request failed ({response.status_code}).{error_suffix}"
            )

        try:
            return response.json()
        except ValueError as error:
            raise FipeRequestError("FIPE API returned invalid JSON.") from error

    @staticmethod
    def _ensure_list(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        raise FipeRequestError("FIPE API returned an unexpected payload format.")

    @staticmethod
    def _resolve_timeout(timeout: float | None) -> float:
        if timeout is not None:
            resolved_timeout = timeout
        else:
            timeout_raw = os.getenv("FIPE_TIMEOUT", str(DEFAULT_TIMEOUT_SECONDS))
            try:
                resolved_timeout = float(timeout_raw)
            except ValueError as error:
                raise FipeRequestError("FIPE_TIMEOUT must be numeric.") from error

        if resolved_timeout <= 0:
            raise FipeRequestError("Request timeout must be greater than zero.")
        return resolved_timeout

    @staticmethod
    def _validate_vehicle_type(vehicle_type: str) -> None:
        if vehicle_type not in ALLOWED_VEHICLE_TYPES:
            allowed = ", ".join(sorted(ALLOWED_VEHICLE_TYPES))
            raise FipeRequestError(
                f"Invalid vehicle_type '{vehicle_type}'. Allowed values: {allowed}."
            )

    @staticmethod
    def _extract_error_message(response: requests.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return ""

        if not isinstance(payload, dict):
            return ""

        for key in ("message", "error", "detail"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""
