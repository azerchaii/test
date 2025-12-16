"""
Use Cases for Procurement Service.
These implement the application business logic for procurement operations.
"""
import uuid
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Tuple

from ...domain.entities.procurement import (
    PurchaseOrder,
    OrderStatus,
    Supplier,
    SupplierMaterial,
    OrderConfirmation,
)
from ..ports.supplier_adapter import SupplierAdapter

logger = logging.getLogger(__name__)


# ==================== DTOs ====================

from dataclasses import dataclass


@dataclass
class ProcessShortageDTO:
    """DTO for processing a material shortage."""
    material_id: str
    material_name: str
    shortage_quantity: int
    triggered_by_request_id: Optional[str] = None


@dataclass
class ProcessShortageResultDTO:
    """Result of processing a shortage."""
    success: bool
    order_id: Optional[str] = None
    message: str = ""
    supplier_name: Optional[str] = None
    estimated_cost: Optional[Decimal] = None


@dataclass
class CreateOrderDTO:
    """DTO for creating a purchase order."""
    material_id: str
    material_name: str
    quantity: int
    supplier_id: Optional[str] = None
    triggered_by_request_id: Optional[str] = None


@dataclass
class OrderDTO:
    """DTO representing a purchase order."""
    id: str
    material_id: str
    material_name: str
    supplier_id: str
    supplier_name: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    status: str
    external_order_id: Optional[str]
    triggered_by_request_id: Optional[str]
    expected_delivery: Optional[str]
    created_at: str


@dataclass
class SupplierDTO:
    """DTO representing a supplier."""
    id: str
    name: str
    email: str
    phone: str
    rating: float
    is_active: bool
    materials: List[dict]
    created_at: str


# ==================== Repository Interface ====================

from abc import ABC, abstractmethod


class PurchaseOrderRepository(ABC):
    """Abstract repository for purchase orders."""

    @abstractmethod
    async def save(self, order: PurchaseOrder) -> PurchaseOrder:
        pass

    @abstractmethod
    async def get_by_id(self, order_id: str) -> Optional[PurchaseOrder]:
        pass

    @abstractmethod
    async def get_all(
        self,
        status: Optional[str] = None,
        supplier_id: Optional[str] = None,
        material_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[PurchaseOrder], int]:
        pass

    @abstractmethod
    async def update(self, order: PurchaseOrder) -> PurchaseOrder:
        pass


class SupplierRepository(ABC):
    """Abstract repository for suppliers."""

    @abstractmethod
    async def get_by_id(self, supplier_id: str) -> Optional[Supplier]:
        pass

    @abstractmethod
    async def get_all(
        self,
        active_only: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Supplier], int]:
        pass

    @abstractmethod
    async def get_for_material(self, material_id: str) -> List[Supplier]:
        pass

    @abstractmethod
    async def save(self, supplier: Supplier) -> Supplier:
        pass

    @abstractmethod
    async def update(self, supplier: Supplier) -> Supplier:
        pass

    @abstractmethod
    async def get_materials(self, supplier_id: str) -> List[SupplierMaterial]:
        pass


# ==================== Use Cases ====================


class SupplierSelector:
    """
    Domain service for selecting the best supplier for a material.
    """

    def select_best_supplier(
        self,
        material_id: str,
        suppliers: List[Supplier],
        supplier_materials: dict,  # supplier_id -> List[SupplierMaterial]
    ) -> Optional[Tuple[Supplier, SupplierMaterial]]:
        """
        Select the best supplier based on:
        1. Availability of the material
        2. Supplier rating
        3. Price (lowest)
        """
        candidates = []

        for supplier in suppliers:
            if not supplier.is_active:
                continue

            materials = supplier_materials.get(supplier.id, [])
            material_info = next(
                (m for m in materials if m.material_id == material_id),
                None
            )

            if material_info:
                candidates.append((supplier, material_info))

        if not candidates:
            return None

        # Sort by: rating (desc), then price (asc)
        candidates.sort(
            key=lambda x: (-x[0].rating, x[1].unit_price)
        )

        return candidates[0]


class ProcessShortageUseCase:
    """
    Use case for automatically processing material shortages.
    This is triggered when inventory detects a shortage.
    """

    def __init__(
        self,
        order_repo: PurchaseOrderRepository,
        supplier_repo: SupplierRepository,
        supplier_adapter: SupplierAdapter,
        notification_client=None,  # gRPC client to notification service
    ):
        self.order_repo = order_repo
        self.supplier_repo = supplier_repo
        self.supplier_adapter = supplier_adapter
        self.notification_client = notification_client
        self.supplier_selector = SupplierSelector()

    async def execute(self, dto: ProcessShortageDTO) -> ProcessShortageResultDTO:
        """
        Process a material shortage by automatically placing an order.
        """
        logger.info(
            f"Processing shortage: material={dto.material_name}, "
            f"quantity={dto.shortage_quantity}"
        )

        # 1. Find suppliers for this material
        suppliers = await self.supplier_repo.get_for_material(dto.material_id)
        if not suppliers:
            return ProcessShortageResultDTO(
                success=False,
                message=f"No suppliers found for material {dto.material_name}",
            )

        # 2. Get supplier materials for pricing
        supplier_materials = {}
        for supplier in suppliers:
            materials = await self.supplier_repo.get_materials(supplier.id)
            supplier_materials[supplier.id] = materials

        # 3. Select best supplier
        selection = self.supplier_selector.select_best_supplier(
            dto.material_id,
            suppliers,
            supplier_materials,
        )

        if not selection:
            return ProcessShortageResultDTO(
                success=False,
                message=f"No active supplier can provide {dto.material_name}",
            )

        supplier, material_info = selection

        # 4. Create purchase order
        order = PurchaseOrder(
            id=str(uuid.uuid4()),
            material_id=dto.material_id,
            material_name=dto.material_name,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            quantity=dto.shortage_quantity,
            unit_price=material_info.unit_price,
            triggered_by_request_id=dto.triggered_by_request_id,
        )
        order.calculate_total()

        # 5. Place order with supplier (via adapter)
        confirmation = await self.supplier_adapter.place_order(supplier, order)

        if not confirmation.is_success:
            order.status = OrderStatus.CANCELLED
            await self.order_repo.save(order)
            return ProcessShortageResultDTO(
                success=False,
                order_id=order.id,
                message=f"Supplier rejected order: {confirmation.error_message}",
                supplier_name=supplier.name,
            )

        # 6. Update order with confirmation details
        order.mark_as_ordered(
            external_order_id=confirmation.external_order_id,
            expected_delivery=confirmation.estimated_delivery or datetime.utcnow(),
        )
        await self.order_repo.save(order)

        # 7. Send notification (if client available)
        if self.notification_client:
            try:
                await self._send_purchase_notification(order, supplier)
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")

        logger.info(
            f"Order placed successfully: id={order.id}, "
            f"supplier={supplier.name}, total={order.total_price}"
        )

        return ProcessShortageResultDTO(
            success=True,
            order_id=order.id,
            message=f"Order placed with {supplier.name}",
            supplier_name=supplier.name,
            estimated_cost=order.total_price,
        )

    async def _send_purchase_notification(
        self,
        order: PurchaseOrder,
        supplier: Supplier,
    ) -> None:
        """Send notification about the purchase."""
        # This would call the notification service via gRPC
        pass


class CreateOrderUseCase:
    """Use case for manually creating a purchase order."""

    def __init__(
        self,
        order_repo: PurchaseOrderRepository,
        supplier_repo: SupplierRepository,
        supplier_adapter: SupplierAdapter,
    ):
        self.order_repo = order_repo
        self.supplier_repo = supplier_repo
        self.supplier_adapter = supplier_adapter

    async def execute(self, dto: CreateOrderDTO) -> Optional[OrderDTO]:
        """Create and place a purchase order."""
        # Get supplier
        supplier = await self.supplier_repo.get_by_id(dto.supplier_id)
        if not supplier:
            raise ValueError(f"Supplier {dto.supplier_id} not found")

        # Get price from adapter
        price = await self.supplier_adapter.get_price(
            dto.supplier_id,
            dto.material_id,
        )
        if not price:
            price = Decimal("0.00")

        # Create order
        order = PurchaseOrder(
            id=str(uuid.uuid4()),
            material_id=dto.material_id,
            material_name=dto.material_name,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            quantity=dto.quantity,
            unit_price=price,
            triggered_by_request_id=dto.triggered_by_request_id,
        )
        order.calculate_total()

        # Place order
        confirmation = await self.supplier_adapter.place_order(supplier, order)
        
        if confirmation.is_success:
            order.mark_as_ordered(
                external_order_id=confirmation.external_order_id,
                expected_delivery=confirmation.estimated_delivery or datetime.utcnow(),
            )
        else:
            order.status = OrderStatus.CANCELLED

        await self.order_repo.save(order)

        return self._order_to_dto(order)

    def _order_to_dto(self, order: PurchaseOrder) -> OrderDTO:
        return OrderDTO(
            id=order.id,
            material_id=order.material_id,
            material_name=order.material_name,
            supplier_id=order.supplier_id,
            supplier_name=order.supplier_name,
            quantity=order.quantity,
            unit_price=order.unit_price,
            total_price=order.total_price,
            status=order.status.value,
            external_order_id=order.external_order_id,
            triggered_by_request_id=order.triggered_by_request_id,
            expected_delivery=order.expected_delivery.isoformat() if order.expected_delivery else None,
            created_at=order.created_at.isoformat(),
        )


class GetOrderUseCase:
    """Use case for getting an order by ID."""

    def __init__(self, order_repo: PurchaseOrderRepository):
        self.order_repo = order_repo

    async def execute(self, order_id: str) -> Optional[OrderDTO]:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            return None
        return self._order_to_dto(order)

    def _order_to_dto(self, order: PurchaseOrder) -> OrderDTO:
        return OrderDTO(
            id=order.id,
            material_id=order.material_id,
            material_name=order.material_name,
            supplier_id=order.supplier_id,
            supplier_name=order.supplier_name,
            quantity=order.quantity,
            unit_price=order.unit_price,
            total_price=order.total_price,
            status=order.status.value,
            external_order_id=order.external_order_id,
            triggered_by_request_id=order.triggered_by_request_id,
            expected_delivery=order.expected_delivery.isoformat() if order.expected_delivery else None,
            created_at=order.created_at.isoformat(),
        )


class UpdateOrderStatusUseCase:
    """Use case for updating order status (e.g., marking as delivered)."""

    def __init__(
        self,
        order_repo: PurchaseOrderRepository,
        inventory_client=None,  # gRPC client to inventory service
    ):
        self.order_repo = order_repo
        self.inventory_client = inventory_client

    async def execute(self, order_id: str, new_status: str) -> Optional[OrderDTO]:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            return None

        old_status = order.status

        # Update status
        if new_status == "DELIVERED":
            order.mark_as_delivered()
            # Update inventory if delivered
            if self.inventory_client:
                try:
                    await self._update_inventory(order)
                except Exception as e:
                    logger.error(f"Failed to update inventory: {e}")
        elif new_status == "CANCELLED":
            order.cancel()
        else:
            order.status = OrderStatus(new_status)
            order.updated_at = datetime.utcnow()

        await self.order_repo.update(order)

        logger.info(f"Order {order_id} status changed: {old_status} -> {new_status}")

        return self._order_to_dto(order)

    async def _update_inventory(self, order: PurchaseOrder) -> None:
        """Update inventory when order is delivered."""
        # This would call inventory service via gRPC to increase stock
        pass

    def _order_to_dto(self, order: PurchaseOrder) -> OrderDTO:
        return OrderDTO(
            id=order.id,
            material_id=order.material_id,
            material_name=order.material_name,
            supplier_id=order.supplier_id,
            supplier_name=order.supplier_name,
            quantity=order.quantity,
            unit_price=order.unit_price,
            total_price=order.total_price,
            status=order.status.value,
            external_order_id=order.external_order_id,
            triggered_by_request_id=order.triggered_by_request_id,
            expected_delivery=order.expected_delivery.isoformat() if order.expected_delivery else None,
            created_at=order.created_at.isoformat(),
        )
