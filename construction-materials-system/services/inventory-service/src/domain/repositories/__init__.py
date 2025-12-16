"""Repository interfaces (Ports)."""
from .material_repository import MaterialRepository, StockMovementRepository, ReservationRepository

__all__ = ["MaterialRepository", "StockMovementRepository", "ReservationRepository"]
