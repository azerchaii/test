"""Data Transfer Objects."""
from .material_dto import (
    CreateMaterialDTO,
    UpdateMaterialDTO,
    MaterialDTO,
    AvailabilityCheckDTO,
    AvailabilityResultDTO,
    ReserveMaterialDTO,
    ReservationResultDTO,
    UpdateStockDTO,
    UpdateStockResultDTO,
    ListMaterialsDTO,
    MaterialListResultDTO,
    MaterialShortageEventDTO,
)

__all__ = [
    "CreateMaterialDTO",
    "UpdateMaterialDTO",
    "MaterialDTO",
    "AvailabilityCheckDTO",
    "AvailabilityResultDTO",
    "ReserveMaterialDTO",
    "ReservationResultDTO",
    "UpdateStockDTO",
    "UpdateStockResultDTO",
    "ListMaterialsDTO",
    "MaterialListResultDTO",
    "MaterialShortageEventDTO",
]
