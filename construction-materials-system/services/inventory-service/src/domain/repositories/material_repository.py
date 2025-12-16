"""
Repository interfaces (Ports) for Inventory Service.
These define the contracts for data persistence, independent of implementation.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from ..entities.material import Material, StockMovement, Reservation


class MaterialRepository(ABC):
    """
    Abstract repository for Material entity.
    Implementations must provide actual data persistence.
    """

    @abstractmethod
    async def get_by_id(self, material_id: str) -> Optional[Material]:
        """Get a material by its ID."""
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Material]:
        """Get a material by its name."""
        pass

    @abstractmethod
    async def get_all(
        self,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Material], int]:
        """
        Get all materials with optional filtering and pagination.
        Returns tuple of (materials, total_count).
        """
        pass

    @abstractmethod
    async def get_low_stock(self) -> List[Material]:
        """Get all materials below their minimum threshold."""
        pass

    @abstractmethod
    async def save(self, material: Material) -> Material:
        """Save a new material or update existing one."""
        pass

    @abstractmethod
    async def update(self, material: Material) -> Material:
        """Update an existing material."""
        pass

    @abstractmethod
    async def delete(self, material_id: str) -> bool:
        """Delete a material by ID. Returns True if deleted."""
        pass

    @abstractmethod
    async def update_quantity(
        self,
        material_id: str,
        delta: int,
        reason: str,
        reference_id: Optional[str] = None
    ) -> Optional[Material]:
        """
        Update the quantity of a material.
        Creates a stock movement record for audit.
        """
        pass

    @abstractmethod
    async def reserve(
        self,
        material_id: str,
        quantity: int,
        request_id: str
    ) -> Optional[str]:
        """
        Reserve a quantity of material for a request.
        Returns reservation_id if successful, None otherwise.
        """
        pass

    @abstractmethod
    async def release_reservation(
        self,
        reservation_id: str
    ) -> bool:
        """
        Release a reservation.
        Returns True if successful.
        """
        pass


class StockMovementRepository(ABC):
    """
    Abstract repository for StockMovement entity.
    Used for audit trail of all stock changes.
    """

    @abstractmethod
    async def save(self, movement: StockMovement) -> StockMovement:
        """Save a new stock movement record."""
        pass

    @abstractmethod
    async def get_by_material(
        self,
        material_id: str,
        limit: int = 100
    ) -> List[StockMovement]:
        """Get stock movements for a specific material."""
        pass

    @abstractmethod
    async def get_by_reference(
        self,
        reference_id: str
    ) -> List[StockMovement]:
        """Get stock movements by reference ID (order, request, etc.)."""
        pass


class ReservationRepository(ABC):
    """
    Abstract repository for Reservation entity.
    Tracks material reservations for requests.
    """

    @abstractmethod
    async def save(self, reservation: Reservation) -> Reservation:
        """Save a new reservation."""
        pass

    @abstractmethod
    async def get_by_id(self, reservation_id: str) -> Optional[Reservation]:
        """Get a reservation by ID."""
        pass

    @abstractmethod
    async def get_by_request(self, request_id: str) -> List[Reservation]:
        """Get all reservations for a request."""
        pass

    @abstractmethod
    async def get_by_material(
        self,
        material_id: str,
        active_only: bool = True
    ) -> List[Reservation]:
        """Get reservations for a material."""
        pass

    @abstractmethod
    async def update_status(
        self,
        reservation_id: str,
        status: str
    ) -> Optional[Reservation]:
        """Update the status of a reservation."""
        pass

    @abstractmethod
    async def cancel(self, reservation_id: str) -> bool:
        """Cancel a reservation and release the reserved quantity."""
        pass
