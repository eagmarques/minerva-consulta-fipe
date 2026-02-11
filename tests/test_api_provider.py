from __future__ import annotations

from typing import Any

import pytest
import requests

from src.providers.api_provider import (
    ApiProvider,
    FipeAuthError,
    FipeNotFoundError,
    FipeRequestError,
    FipeServerError,
    FipeSubscriptionError,
)


class DummyResponse:
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class DummySession:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> DummyResponse:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "params": params,
                "timeout": timeout,
            }
        )
        payload = self.responses.pop(0)
        if isinstance(payload, Exception):
            raise payload
        return payload


def test_missing_token_raises_auth_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FIPE_TOKEN", raising=False)
    with pytest.raises(FipeAuthError):
        ApiProvider(token=None, session=DummySession([]))


def test_invalid_timeout_env_raises_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIPE_TOKEN", "secret")
    monkeypatch.setenv("FIPE_TIMEOUT", "not-a-number")

    with pytest.raises(FipeRequestError, match="FIPE_TIMEOUT must be numeric"):
        ApiProvider(token=None, session=DummySession([]))


def test_non_positive_timeout_raises_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIPE_TOKEN", "secret")

    with pytest.raises(FipeRequestError, match="greater than zero"):
        ApiProvider(token=None, timeout=0, session=DummySession([]))


def test_list_references(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIPE_TOKEN", "secret")
    session = DummySession([DummyResponse(200, [{"code": "320", "month": "abril de 2024"}])])
    provider = ApiProvider(session=session)

    result = provider.list_references()

    assert len(result) == 1
    assert result[0].code == "320"
    assert result[0].month == "abril de 2024"
    assert session.calls[0]["headers"] == {"X-Subscription-Token": "secret"}


def test_list_brands_with_reference_param(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIPE_TOKEN", "secret")
    session = DummySession([DummyResponse(200, [{"code": "1", "name": "Ford"}])])
    provider = ApiProvider(session=session)

    result = provider.list_brands("cars", "320")

    assert len(result) == 1
    assert result[0].name == "Ford"
    assert session.calls[0]["params"] == {"reference": "320"}


def test_invalid_vehicle_type_raises_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIPE_TOKEN", "secret")
    session = DummySession([])
    provider = ApiProvider(session=session)

    with pytest.raises(FipeRequestError, match="Invalid vehicle_type"):
        provider.list_brands("boats", "320")

    assert session.calls == []


def test_list_models_from_dict_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIPE_TOKEN", "secret")
    session = DummySession(
        [DummyResponse(200, {"models": [{"code": "100", "name": "Focus"}], "years": []})]
    )
    provider = ApiProvider(session=session)

    result = provider.list_models("cars", "1", "320")

    assert len(result) == 1
    assert result[0].code == "100"


def test_list_years(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIPE_TOKEN", "secret")
    session = DummySession([DummyResponse(200, [{"code": "2014-1", "name": "2014 Gasolina"}])])
    provider = ApiProvider(session=session)

    result = provider.list_years("cars", "1", "100", "320")

    assert len(result) == 1
    assert result[0].name == "2014 Gasolina"


def test_get_price(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIPE_TOKEN", "secret")
    session = DummySession(
        [
            DummyResponse(
                200,
                {
                    "price": "R$ 45.000,00",
                    "brand": "Ford",
                    "model": "Focus",
                    "fuel": "Gasolina",
                    "modelYear": 2014,
                    "codeFipe": "003001-0",
                    "referenceMonth": "abril de 2024",
                    "authentication": "abc123",
                },
            )
        ]
    )
    provider = ApiProvider(session=session)

    result = provider.get_price("cars", "1", "100", "2014-1", "320")

    assert result.code_fipe == "003001-0"
    assert result.price == "R$ 45.000,00"
    assert result.authentication == "abc123"


def test_http_404_raises_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIPE_TOKEN", "secret")
    provider = ApiProvider(session=DummySession([DummyResponse(404, {"message": "Not found"})]))

    with pytest.raises(FipeNotFoundError):
        provider.list_references()


def test_http_500_raises_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIPE_TOKEN", "secret")
    provider = ApiProvider(session=DummySession([DummyResponse(500, {"message": "Error"})]))

    with pytest.raises(FipeServerError):
        provider.list_references()


def test_http_401_raises_auth_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIPE_TOKEN", "secret")
    provider = ApiProvider(session=DummySession([DummyResponse(401, {"message": "Unauthorized"})]))

    with pytest.raises(FipeAuthError):
        provider.list_references()


def test_http_402_raises_subscription_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIPE_TOKEN", "secret")
    provider = ApiProvider(
        session=DummySession([DummyResponse(402, {"message": "Payment required"})])
    )

    with pytest.raises(FipeSubscriptionError):
        provider.list_references()


def test_http_400_includes_api_error_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIPE_TOKEN", "secret")
    provider = ApiProvider(
        session=DummySession([DummyResponse(400, {"message": "Invalid reference"})])
    )

    with pytest.raises(FipeRequestError, match="Invalid reference"):
        provider.list_references()


def test_timeout_raises_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIPE_TOKEN", "secret")
    provider = ApiProvider(session=DummySession([requests.Timeout("timeout")]))

    with pytest.raises(FipeRequestError):
        provider.list_references()


def test_invalid_json_raises_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIPE_TOKEN", "secret")
    provider = ApiProvider(session=DummySession([DummyResponse(200, ValueError("invalid"))]))

    with pytest.raises(FipeRequestError):
        provider.list_references()


def test_invalid_list_payload_raises_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIPE_TOKEN", "secret")
    provider = ApiProvider(session=DummySession([DummyResponse(200, {"unexpected": "payload"})]))

    with pytest.raises(FipeRequestError):
        provider.list_references()
