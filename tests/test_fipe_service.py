from __future__ import annotations

from src.domain.models import Brand, ModelYear, PriceResult, Reference, VehicleModel
from src.providers.base import FipeProvider
from src.services.fipe_service import FipeService


class FakeProvider(FipeProvider):
    def list_references(self) -> list[Reference]:
        return [Reference(code="320", month="Abril de 2024")]

    def list_brands(self, vehicle_type: str, reference: str) -> list[Brand]:
        return [Brand(code="1", name=f"{vehicle_type}-{reference}")]

    def list_models(self, vehicle_type: str, brand_id: str, reference: str) -> list[VehicleModel]:
        return [VehicleModel(code="100", name=f"{brand_id}-{reference}")]

    def list_years(
        self,
        vehicle_type: str,
        brand_id: str,
        model_id: str,
        reference: str,
    ) -> list[ModelYear]:
        return [ModelYear(code="2014-1", name=f"{model_id}-{reference}")]

    def get_price(
        self,
        vehicle_type: str,
        brand_id: str,
        model_id: str,
        year_id: str,
        reference: str,
    ) -> PriceResult:
        return PriceResult(
            price="",
            code_fipe="003001-0",
            brand="Ford",
            model="Focus",
            fuel="Gasolina",
            model_year=2014,
            reference_month="Abril de 2024",
            price_value=45000.0,
        )


def test_list_references_normalizes_month() -> None:
    service = FipeService(provider=FakeProvider())

    result = service.list_references()

    assert result[0].month == "abril de 2024"


def test_list_entities_passthrough() -> None:
    service = FipeService(provider=FakeProvider())

    brands = service.list_brands("cars", "320")
    models = service.list_models("cars", "1", "320")
    years = service.list_years("cars", "1", "100", "320")

    assert brands[0].name == "cars-320"
    assert models[0].name == "1-320"
    assert years[0].name == "100-320"


def test_get_price_formats_fallback_and_normalizes_month() -> None:
    service = FipeService(provider=FakeProvider())

    result = service.get_price("cars", "1", "100", "2014-1", "320")

    assert result.price == "R$ 45.000,00"
    assert result.reference_month == "abril de 2024"
