"""
Data Transfer Objects for Material operations.
DTOs are used to transfer data between layers and to/from external interfaces.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class CreateMaterialDTO:
    """DTO for creating a new material."""
    name: str
    unit: str
    category: str
    initial_quantity: int = 0
    min_threshold: int = 10


@dataclass
class UpdateMaterialDTO:
    """DTO for updating a material."""
    material_id: str
    name: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    min_threshold: Optional[int] = None


@dataclass
class MaterialDTO:
    """DTO representing a material for external interfaces."""
    id: str
    name: str
    unit: str
    category: str
    quantity: int
    reserved: int
    available: int
    min_threshold: int
    is_low_stock: bool
    created_at: str
    updated_at: str


@dataclass
class AvailabilityCheckDTO:
    """DTO for checking material availability."""
    material_id: str
    requested_quantity: int


@dataclass
class AvailabilityResultDTO:
    """DTO for availability check result."""
    material_id: str
    material_name: str
    is_available: bool
    available_quantity: int
    requested_quantity: int
    shortage: int


@dataclass
class ReserveMaterialDTO:
    """DTO for reserving material."""
    material_id: str
    quantity: int
    request_id: str


@dataclass
class ReservationResultDTO:
    """DTO for reservation result."""
    success: bool
    reservation_id: Optional[str] = None
    reserved_quantity: int = 0
    error_message: Optional[str] = None


@dataclass
class UpdateStockDTO:
    """DTO for updating stock quantity."""
    material_id: str
    quantity_delta: int
    reason: str
    reference_id: Optional[str] = None


@dataclass
class UpdateStockResultDTO:
    """DTO for stock update result."""
    success: bool
    new_quantity: int = 0
    error_message: Optional[str] = None


@dataclass
class ListMaterialsDTO:
    """DTO for list materials request."""
    category: Optional[str] = None
    page: int = 1
    page_size: int = 20


@dataclass
class MaterialListResultDTO:
    """DTO for list materials response."""
    materials: List[MaterialDTO]
    total_count: int
    page: int
    page_size: int


@dataclass
class MaterialShortageEventDTO:
    """DTO for material shortage event (to be published to message queue)."""
    material_id: str
    material_name: str
    current_quantity: int
    requested_quantity: int
    shortage: int
    triggered_by_request_id: Optional[str] = None
    timestamp: str = ""
