"""
Supplier Adapter Port - Interface for interacting with supplier systems.
This is an application-level port that infrastructure adapters will implement.
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from ...domain.entities.procurement import OrderConfirmation, Supplier, PurchaseOrder


class SupplierAdapter(ABC):
    """
    Abstract interface for supplier integration.
    Implementations can be:
    - StubSupplierAdapter: For testing without real suppliers
    - RealSupplierAdapter: For production with actual supplier APIs
    """

    @abstractmethod
    async def place_order(
        self,
        supplier: Supplier,
        order: PurchaseOrder,
    ) -> OrderConfirmation:
        """
        Place an order with the supplier.
        
        Args:
            supplier: The supplier to order from
            order: The purchase order details
            
        Returns:
            OrderConfirmation with status and external order ID
        """
        pass

    @abstractmethod
    async def get_price(
        self,
        supplier_id: str,
        material_id: str,
    ) -> Optional[Decimal]:
        """
        Get the current price for a material from a supplier.
        
        Args:
            supplier_id: The supplier's ID
            material_id: The material's ID
            
        Returns:
            The unit price or None if not available
        """
        pass

    @abstractmethod
    async def check_availability(
        self,
        supplier_id: str,
        material_id: str,
        quantity: int,
    ) -> bool:
        """
        Check if a supplier can fulfill the requested quantity.
        
        Args:
            supplier_id: The supplier's ID
            material_id: The material's ID
            quantity: Requested quantity
            
        Returns:
            True if available, False otherwise
        """
        pass

    @abstractmethod
    async def cancel_order(
        self,
        supplier: Supplier,
        external_order_id: str,
    ) -> bool:
        """
        Cancel an existing order with the supplier.
        
        Args:
            supplier: The supplier
            external_order_id: The supplier's order ID
            
        Returns:
            True if cancelled successfully
        """
        pass
