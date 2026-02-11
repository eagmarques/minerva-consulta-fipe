from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Reference:
    code: str
    month: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Reference:
        return cls(
            code=str(payload.get("code", "")),
            month=str(payload.get("month") or payload.get("name") or ""),
        )


@dataclass(frozen=True)
class Brand:
    code: str
    name: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Brand:
        return cls(
            code=str(payload.get("code", "")),
            name=str(payload.get("name", "")),
        )


@dataclass(frozen=True)
class VehicleModel:
    code: str
    name: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> VehicleModel:
        return cls(
            code=str(payload.get("code", "")),
            name=str(payload.get("name", "")),
        )


@dataclass(frozen=True)
class ModelYear:
    code: str
    name: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ModelYear:
        return cls(
            code=str(payload.get("code", "")),
            name=str(payload.get("name", "")),
        )


@dataclass(frozen=True)
class PriceResult:
    price: str
    code_fipe: str
    brand: str
    model: str
    fuel: str
    model_year: int | None
    reference_month: str
    authentication: str = ""
    price_value: float | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PriceResult:
        model_year_raw = payload.get("modelYear")
        model_year = int(model_year_raw) if model_year_raw is not None else None

        price_value_raw = payload.get("priceValue")
        price_value = float(price_value_raw) if price_value_raw is not None else None

        return cls(
            price=str(payload.get("price", "")),
            code_fipe=str(payload.get("codeFipe", "")),
            brand=str(payload.get("brand", "")),
            model=str(payload.get("model", "")),
            fuel=str(payload.get("fuel", "")),
            model_year=model_year,
            reference_month=str(payload.get("referenceMonth", "")),
            authentication=str(payload.get("authentication", "")),
            price_value=price_value,
        )

    def to_display_dict(self) -> dict[str, Any]:
        return {
            "price": self.price,
            "codeFipe": self.code_fipe,
            "brand": self.brand,
            "model": self.model,
            "fuel": self.fuel,
            "modelYear": self.model_year,
            "referenceMonth": self.reference_month,
            "authentication": self.authentication,
        }
