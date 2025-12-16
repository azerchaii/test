"""
Domain Layer - Core business logic and entities.
This layer is independent of any external frameworks or databases.
"""
from .entities.material import (
    Material,
    MaterialUnit,
    StockMovement,
    StockUpdateReason,
    Reservation,
)
from .repositories.material_repository import (
    MaterialRepository,
    StockMovementRepository,
    ReservationRepository,
)

__all__ = [
    "Material",
    "MaterialUnit",
    "StockMovement",
    "StockUpdateReason",
    "Reservation",
    "MaterialRepository",
    "StockMovementRepository",
    "ReservationRepository",
]
