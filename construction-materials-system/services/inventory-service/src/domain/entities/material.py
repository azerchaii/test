"""
Domain entities for Inventory Service.
These are the core business objects, independent of any framework or database.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class MaterialUnit(str, Enum):
    """Units of measurement for materials."""
    PIECES = "pieces"
    METERS = "meters"
    KILOGRAMS = "kg"
    LITERS = "liters"
    CUBIC_METERS = "m3"
    SQUARE_METERS = "m2"


class StockUpdateReason(str, Enum):
    """Reasons for stock quantity changes."""
    PURCHASE = "PURCHASE"
    MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT"
    CONSUMPTION = "CONSUMPTION"
    RESERVATION = "RESERVATION"
    RELEASE = "RELEASE"
    INITIAL = "INITIAL"


@dataclass
class Material:
    """
    Material entity - represents a construction material in the system.
    """
    id: str
    name: str
    unit: MaterialUnit
    category: str
    quantity: int = 0
    reserved: int = 0
    min_threshold: int = 10
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def available(self) -> int:
        """Returns the quantity available for reservation (total - reserved)."""
        return max(0, self.quantity - self.reserved)

    @property
    def is_low_stock(self) -> bool:
        """Check if material is below minimum threshold."""
        return self.available < self.min_threshold

    def can_reserve(self, quantity: int) -> bool:
        """Check if the requested quantity can be reserved."""
        return self.available >= quantity

    def reserve(self, quantity: int) -> bool:
        """
        Reserve a quantity of material.
        Returns True if successful, False otherwise.
        """
        if not self.can_reserve(quantity):
            return False
        self.reserved += quantity
        self.updated_at = datetime.utcnow()
        return True

    def release(self, quantity: int) -> bool:
        """
        Release a reserved quantity.
        Returns True if successful, False otherwise.
        """
        if quantity > self.reserved:
            return False
        self.reserved -= quantity
        self.updated_at = datetime.utcnow()
        return True

    def update_quantity(self, delta: int, reason: StockUpdateReason) -> int:
        """
        Update the quantity by delta (can be positive or negative).
        Returns the new quantity.
        """
        self.quantity = max(0, self.quantity + delta)
        self.updated_at = datetime.utcnow()
        return self.quantity


@dataclass
class StockMovement:
    """
    Records a movement/change in stock quantity.
    Used for audit trail and history.
    """
    id: str
    material_id: str
    quantity_delta: int
    reason: StockUpdateReason
    reference_id: Optional[str] = None  # order_id, request_id, etc.
    created_at: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


@dataclass
class Reservation:
    """
    Represents a reservation of materials for a specific request.
    """
    id: str
    material_id: str
    request_id: str
    quantity: int
    status: str = "ACTIVE"  # ACTIVE, FULFILLED, CANCELLED
    created_at: datetime = field(default_factory=datetime.utcnow)
    fulfilled_at: Optional[datetime] = None
