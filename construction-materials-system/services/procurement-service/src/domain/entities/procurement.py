"""
Domain entities for Procurement Service.
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum


class OrderStatus(str, Enum):
    """Status of a purchase order."""
    PENDING = "PENDING"
    ORDERED = "ORDERED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


@dataclass
class Supplier:
    """
    Supplier entity - represents a material supplier.
    """
    id: str
    name: str
    email: str
    phone: str = ""
    rating: float = 5.0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    def can_supply(self, material_id: str, materials: List["SupplierMaterial"]) -> bool:
        """Check if supplier can supply a specific material."""
        return any(m.material_id == material_id for m in materials)


@dataclass
class SupplierMaterial:
    """
    Material that a supplier can provide with pricing.
    """
    id: str
    supplier_id: str
    material_id: str
    material_name: str = ""
    unit_price: Decimal = Decimal("0.00")


@dataclass
class PurchaseOrder:
    """
    Purchase Order entity - represents an order placed with a supplier.
    """
    id: str
    material_id: str
    material_name: str
    supplier_id: str
    supplier_name: str = ""
    quantity: int = 0
    unit_price: Decimal = Decimal("0.00")
    total_price: Decimal = Decimal("0.00")
    status: OrderStatus = OrderStatus.PENDING
    external_order_id: Optional[str] = None
    triggered_by_request_id: Optional[str] = None
    expected_delivery: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def calculate_total(self) -> Decimal:
        """Calculate total price."""
        self.total_price = self.unit_price * self.quantity
        return self.total_price

    def mark_as_ordered(self, external_order_id: str, expected_delivery: datetime) -> None:
        """Mark order as placed with supplier."""
        self.status = OrderStatus.ORDERED
        self.external_order_id = external_order_id
        self.expected_delivery = expected_delivery
        self.updated_at = datetime.utcnow()

    def mark_as_delivered(self) -> None:
        """Mark order as delivered."""
        self.status = OrderStatus.DELIVERED
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """Cancel the order."""
        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.utcnow()


@dataclass
class OrderConfirmation:
    """
    Confirmation received from supplier after placing an order.
    """
    order_id: str
    external_order_id: str
    status: str
    estimated_delivery: Optional[datetime] = None
    error_message: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.status in ("CONFIRMED", "ACCEPTED", "SUCCESS")
