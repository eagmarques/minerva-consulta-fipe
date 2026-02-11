from __future__ import annotations

from dataclasses import replace

from src.domain.models import Brand, ModelYear, PriceResult, Reference, VehicleModel
from src.providers.base import FipeProvider
from src.utils.formatting import coalesce_price_display, normalize_reference_month


class FipeService:
    def __init__(self, provider: FipeProvider) -> None:
        self.provider = provider

    def list_references(self) -> list[Reference]:
        references = self.provider.list_references()
        return [replace(item, month=normalize_reference_month(item.month)) for item in references]

    def list_recent_references(self, limit: int = 3) -> list[Reference]:
        if limit <= 0:
            return []

        references = self.list_references()
        return sorted(references, key=self._reference_sort_key, reverse=True)[:limit]

    def list_brands(self, vehicle_type: str, reference: str) -> list[Brand]:
        return self.provider.list_brands(vehicle_type=vehicle_type, reference=reference)

    def list_models(self, vehicle_type: str, brand_id: str, reference: str) -> list[VehicleModel]:
        return self.provider.list_models(
            vehicle_type=vehicle_type,
            brand_id=brand_id,
            reference=reference,
        )

    def list_years(
        self,
        vehicle_type: str,
        brand_id: str,
        model_id: str,
        reference: str,
    ) -> list[ModelYear]:
        return self.provider.list_years(
            vehicle_type=vehicle_type,
            brand_id=brand_id,
            model_id=model_id,
            reference=reference,
        )

    def get_price(
        self,
        vehicle_type: str,
        brand_id: str,
        model_id: str,
        year_id: str,
        reference: str,
    ) -> PriceResult:
        result = self.provider.get_price(
            vehicle_type=vehicle_type,
            brand_id=brand_id,
            model_id=model_id,
            year_id=year_id,
            reference=reference,
        )
        normalized_month = normalize_reference_month(result.reference_month)
        normalized_price = coalesce_price_display(result.price, result.price_value)
        return replace(
            result,
            reference_month=normalized_month,
            price=normalized_price,
        )

    @staticmethod
    def _reference_sort_key(reference: Reference) -> int:
        try:
            return int(reference.code)
        except ValueError:
            return -1
