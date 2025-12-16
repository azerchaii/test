"""
Use Cases for Inventory Service.
These implement the application business logic, orchestrating domain entities and repositories.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from ...domain.entities.material import Material, MaterialUnit, StockUpdateReason
from ...domain.repositories.material_repository import (
    MaterialRepository,
    StockMovementRepository,
    ReservationRepository,
)
from ..dto.material_dto import (
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
from ..ports.message_publisher import MessagePublisher


def _material_to_dto(material: Material) -> MaterialDTO:
    """Convert Material entity to DTO."""
    return MaterialDTO(
        id=material.id,
        name=material.name,
        unit=material.unit.value,
        category=material.category,
        quantity=material.quantity,
        reserved=material.reserved,
        available=material.available,
        min_threshold=material.min_threshold,
        is_low_stock=material.is_low_stock,
        created_at=material.created_at.isoformat(),
        updated_at=material.updated_at.isoformat(),
    )


class CreateMaterialUseCase:
    """Use case for creating a new material."""

    def __init__(self, material_repo: MaterialRepository):
        self.material_repo = material_repo

    async def execute(self, dto: CreateMaterialDTO) -> MaterialDTO:
        # Check if material with same name already exists
        existing = await self.material_repo.get_by_name(dto.name)
        if existing:
            raise ValueError(f"Material with name '{dto.name}' already exists")

        # Create new material entity
        material = Material(
            id=str(uuid.uuid4()),
            name=dto.name,
            unit=MaterialUnit(dto.unit),
            category=dto.category,
            quantity=dto.initial_quantity,
            min_threshold=dto.min_threshold,
        )

        # Save to repository
        saved_material = await self.material_repo.save(material)
        return _material_to_dto(saved_material)


class GetMaterialUseCase:
    """Use case for getting a material by ID."""

    def __init__(self, material_repo: MaterialRepository):
        self.material_repo = material_repo

    async def execute(self, material_id: str) -> Optional[MaterialDTO]:
        material = await self.material_repo.get_by_id(material_id)
        if not material:
            return None
        return _material_to_dto(material)


class ListMaterialsUseCase:
    """Use case for listing materials with pagination."""

    def __init__(self, material_repo: MaterialRepository):
        self.material_repo = material_repo

    async def execute(self, dto: ListMaterialsDTO) -> MaterialListResultDTO:
        materials, total = await self.material_repo.get_all(
            category=dto.category,
            page=dto.page,
            page_size=dto.page_size,
        )

        return MaterialListResultDTO(
            materials=[_material_to_dto(m) for m in materials],
            total_count=total,
            page=dto.page,
            page_size=dto.page_size,
        )


class UpdateMaterialUseCase:
    """Use case for updating a material."""

    def __init__(self, material_repo: MaterialRepository):
        self.material_repo = material_repo

    async def execute(self, dto: UpdateMaterialDTO) -> Optional[MaterialDTO]:
        material = await self.material_repo.get_by_id(dto.material_id)
        if not material:
            return None

        # Update fields if provided
        if dto.name is not None:
            material.name = dto.name
        if dto.unit is not None:
            material.unit = MaterialUnit(dto.unit)
        if dto.category is not None:
            material.category = dto.category
        if dto.min_threshold is not None:
            material.min_threshold = dto.min_threshold

        material.updated_at = datetime.utcnow()

        updated = await self.material_repo.update(material)
        return _material_to_dto(updated)


class CheckAvailabilityUseCase:
    """
    Use case for checking material availability.
    If shortage is detected, publishes an event to trigger auto-procurement.
    """

    def __init__(
        self,
        material_repo: MaterialRepository,
        message_publisher: Optional[MessagePublisher] = None,
    ):
        self.material_repo = material_repo
        self.message_publisher = message_publisher

    async def execute(
        self,
        dto: AvailabilityCheckDTO,
        request_id: Optional[str] = None,
        publish_shortage: bool = True,
    ) -> AvailabilityResultDTO:
        material = await self.material_repo.get_by_id(dto.material_id)
        if not material:
            raise ValueError(f"Material with ID '{dto.material_id}' not found")

        is_available = material.available >= dto.requested_quantity
        shortage = max(0, dto.requested_quantity - material.available)

        result = AvailabilityResultDTO(
            material_id=material.id,
            material_name=material.name,
            is_available=is_available,
            available_quantity=material.available,
            requested_quantity=dto.requested_quantity,
            shortage=shortage,
        )

        # Publish shortage event if there's a shortage and publisher is configured
        if shortage > 0 and publish_shortage and self.message_publisher:
            event = MaterialShortageEventDTO(
                material_id=material.id,
                material_name=material.name,
                current_quantity=material.available,
                requested_quantity=dto.requested_quantity,
                shortage=shortage,
                triggered_by_request_id=request_id,
                timestamp=datetime.utcnow().isoformat(),
            )
            await self.message_publisher.publish(
                exchange="materials.events",
                routing_key="material.shortage",
                message=event.__dict__,
            )

        return result


class ReserveMaterialUseCase:
    """Use case for reserving material for a request."""

    def __init__(self, material_repo: MaterialRepository):
        self.material_repo = material_repo

    async def execute(self, dto: ReserveMaterialDTO) -> ReservationResultDTO:
        material = await self.material_repo.get_by_id(dto.material_id)
        if not material:
            return ReservationResultDTO(
                success=False,
                error_message=f"Material with ID '{dto.material_id}' not found",
            )

        if not material.can_reserve(dto.quantity):
            return ReservationResultDTO(
                success=False,
                error_message=f"Insufficient quantity. Available: {material.available}, Requested: {dto.quantity}",
            )

        reservation_id = await self.material_repo.reserve(
            material_id=dto.material_id,
            quantity=dto.quantity,
            request_id=dto.request_id,
        )

        if reservation_id:
            return ReservationResultDTO(
                success=True,
                reservation_id=reservation_id,
                reserved_quantity=dto.quantity,
            )
        else:
            return ReservationResultDTO(
                success=False,
                error_message="Failed to create reservation",
            )


class ReleaseReservationUseCase:
    """Use case for releasing a material reservation."""

    def __init__(self, material_repo: MaterialRepository):
        self.material_repo = material_repo

    async def execute(self, reservation_id: str) -> bool:
        return await self.material_repo.release_reservation(reservation_id)


class UpdateStockUseCase:
    """
    Use case for updating stock quantity.
    Used after purchase delivery or manual adjustment.
    """

    def __init__(
        self,
        material_repo: MaterialRepository,
        message_publisher: Optional[MessagePublisher] = None,
    ):
        self.material_repo = material_repo
        self.message_publisher = message_publisher

    async def execute(self, dto: UpdateStockDTO) -> UpdateStockResultDTO:
        material = await self.material_repo.update_quantity(
            material_id=dto.material_id,
            delta=dto.quantity_delta,
            reason=dto.reason,
            reference_id=dto.reference_id,
        )

        if material:
            # Publish stock updated event
            if self.message_publisher:
                await self.message_publisher.publish(
                    exchange="materials.events",
                    routing_key="stock.updated",
                    message={
                        "material_id": material.id,
                        "material_name": material.name,
                        "new_quantity": material.quantity,
                        "delta": dto.quantity_delta,
                        "reason": dto.reason,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

            return UpdateStockResultDTO(
                success=True,
                new_quantity=material.quantity,
            )
        else:
            return UpdateStockResultDTO(
                success=False,
                error_message=f"Material with ID '{dto.material_id}' not found",
            )


class GetLowStockMaterialsUseCase:
    """Use case for getting materials below threshold."""

    def __init__(self, material_repo: MaterialRepository):
        self.material_repo = material_repo

    async def execute(self) -> List[MaterialDTO]:
        materials = await self.material_repo.get_low_stock()
        return [_material_to_dto(m) for m in materials]
