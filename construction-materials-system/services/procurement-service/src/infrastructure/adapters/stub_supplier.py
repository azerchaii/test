"""
Stub Supplier Adapter - For testing without real supplier integrations.

This adapter simulates supplier behavior for development and testing purposes.
It stores all "placed" orders in memory and can simulate various scenarios
like delays, failures, and price variations.
"""
import uuid
import random
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any

from ...application.ports.supplier_adapter import SupplierAdapter
from ...domain.entities.procurement import OrderConfirmation, Supplier, PurchaseOrder

logger = logging.getLogger(__name__)


class StubSupplierAdapter(SupplierAdapter):
    """
    Stub implementation of SupplierAdapter for testing.
    
    Features:
    - Configurable failure rate for testing error handling
    - Configurable base prices
    - In-memory order history for verification in tests
    - Simulated delivery times
    
    Usage:
        # Basic usage
        adapter = StubSupplierAdapter()
        
        # With custom configuration
        adapter = StubSupplierAdapter(
            failure_rate=0.1,  # 10% chance of failure
            base_price=Decimal("150.00"),
            min_delivery_days=2,
            max_delivery_days=7,
        )
        
        # Access order history for testing
        orders = adapter.get_order_history()
        adapter.clear_history()
    """

    def __init__(
        self,
        failure_rate: float = 0.0,
        base_price: Decimal = Decimal("100.00"),
        min_delivery_days: int = 2,
        max_delivery_days: int = 7,
        log_to_console: bool = True,
    ):
        """
        Initialize the stub adapter.
        
        Args:
            failure_rate: Probability of order failure (0.0 to 1.0)
            base_price: Base price for materials (varied by material)
            min_delivery_days: Minimum days for delivery estimate
            max_delivery_days: Maximum days for delivery estimate
            log_to_console: Whether to log operations to console
        """
        self.failure_rate = failure_rate
        self.base_price = base_price
        self.min_delivery_days = min_delivery_days
        self.max_delivery_days = max_delivery_days
        self.log_to_console = log_to_console
        
        # In-memory storage for testing
        self._orders_placed: List[Dict[str, Any]] = []
        self._cancelled_orders: List[str] = []
        
        # Material price variations (for more realistic testing)
        self._price_variations: Dict[str, Decimal] = {}

    async def place_order(
        self,
        supplier: Supplier,
        order: PurchaseOrder,
    ) -> OrderConfirmation:
        """
        Simulate placing an order with a supplier.
        """
        self._log(
            f"Placing order: supplier={supplier.name}, "
            f"material={order.material_name}, qty={order.quantity}"
        )

        # Simulate random failures
        if random.random() < self.failure_rate:
            self._log(f"Simulated failure for order {order.id}")
            return OrderConfirmation(
                order_id=order.id,
                external_order_id="",
                status="FAILED",
                error_message="Simulated supplier error - please retry",
            )

        # Generate external order ID
        external_order_id = f"STUB-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate estimated delivery
        delivery_days = random.randint(self.min_delivery_days, self.max_delivery_days)
        estimated_delivery = datetime.utcnow() + timedelta(days=delivery_days)

        # Store order for testing verification
        order_record = {
            "order_id": order.id,
            "external_order_id": external_order_id,
            "supplier_id": supplier.id,
            "supplier_name": supplier.name,
            "material_id": order.material_id,
            "material_name": order.material_name,
            "quantity": order.quantity,
            "unit_price": float(order.unit_price),
            "total_price": float(order.total_price),
            "estimated_delivery": estimated_delivery.isoformat(),
            "placed_at": datetime.utcnow().isoformat(),
            "status": "CONFIRMED",
        }
        self._orders_placed.append(order_record)

        self._log(
            f"Order confirmed: external_id={external_order_id}, "
            f"delivery={estimated_delivery.date()}"
        )

        return OrderConfirmation(
            order_id=order.id,
            external_order_id=external_order_id,
            status="CONFIRMED",
            estimated_delivery=estimated_delivery,
        )

    async def get_price(
        self,
        supplier_id: str,
        material_id: str,
    ) -> Optional[Decimal]:
        """
        Get a simulated price for a material.
        Prices vary slightly by material for more realistic testing.
        """
        # Generate consistent but varied prices per material
        if material_id not in self._price_variations:
            variation = Decimal(str(random.uniform(0.8, 1.5)))
            self._price_variations[material_id] = self.base_price * variation

        price = self._price_variations[material_id].quantize(Decimal("0.01"))
        self._log(f"Price check: supplier={supplier_id}, material={material_id}, price={price}")
        return price

    async def check_availability(
        self,
        supplier_id: str,
        material_id: str,
        quantity: int,
    ) -> bool:
        """
        Check simulated availability.
        90% of materials are available by default.
        """
        available = random.random() > 0.1
        self._log(
            f"Availability check: supplier={supplier_id}, material={material_id}, "
            f"qty={quantity}, available={available}"
        )
        return available

    async def cancel_order(
        self,
        supplier: Supplier,
        external_order_id: str,
    ) -> bool:
        """
        Simulate order cancellation.
        """
        # Check if order exists
        order_exists = any(
            o["external_order_id"] == external_order_id
            for o in self._orders_placed
        )
        
        if not order_exists:
            self._log(f"Cancel failed: order {external_order_id} not found")
            return False

        # Mark as cancelled
        self._cancelled_orders.append(external_order_id)
        
        # Update order status in history
        for order in self._orders_placed:
            if order["external_order_id"] == external_order_id:
                order["status"] = "CANCELLED"
                break

        self._log(f"Order cancelled: {external_order_id}")
        return True

    # ==================== Testing Helper Methods ====================

    def get_order_history(self) -> List[Dict[str, Any]]:
        """Get all placed orders (for testing verification)."""
        return self._orders_placed.copy()

    def get_orders_for_supplier(self, supplier_id: str) -> List[Dict[str, Any]]:
        """Get orders for a specific supplier."""
        return [o for o in self._orders_placed if o["supplier_id"] == supplier_id]

    def get_orders_for_material(self, material_id: str) -> List[Dict[str, Any]]:
        """Get orders for a specific material."""
        return [o for o in self._orders_placed if o["material_id"] == material_id]

    def get_cancelled_orders(self) -> List[str]:
        """Get list of cancelled order IDs."""
        return self._cancelled_orders.copy()

    def clear_history(self) -> None:
        """Clear all order history (for test cleanup)."""
        self._orders_placed.clear()
        self._cancelled_orders.clear()
        self._price_variations.clear()

    def set_price_for_material(self, material_id: str, price: Decimal) -> None:
        """Set a specific price for a material (for testing)."""
        self._price_variations[material_id] = price

    def simulate_delivery(self, external_order_id: str) -> bool:
        """Mark an order as delivered (for testing)."""
        for order in self._orders_placed:
            if order["external_order_id"] == external_order_id:
                order["status"] = "DELIVERED"
                order["delivered_at"] = datetime.utcnow().isoformat()
                return True
        return False

    def _log(self, message: str) -> None:
        """Log a message if logging is enabled."""
        if self.log_to_console:
            logger.info(f"[STUB SUPPLIER] {message}")
