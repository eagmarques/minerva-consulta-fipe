from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.models import Brand, ModelYear, PriceResult, Reference, VehicleModel


class FipeProvider(ABC):
    @abstractmethod
    def list_references(self) -> list[Reference]:
        raise NotImplementedError

    @abstractmethod
    def list_brands(self, vehicle_type: str, reference: str) -> list[Brand]:
        raise NotImplementedError

    @abstractmethod
    def list_models(self, vehicle_type: str, brand_id: str, reference: str) -> list[VehicleModel]:
        raise NotImplementedError

    @abstractmethod
    def list_years(
        self,
        vehicle_type: str,
        brand_id: str,
        model_id: str,
        reference: str,
    ) -> list[ModelYear]:
        raise NotImplementedError

    @abstractmethod
    def get_price(
        self,
        vehicle_type: str,
        brand_id: str,
        model_id: str,
        year_id: str,
        reference: str,
    ) -> PriceResult:
        raise NotImplementedError
