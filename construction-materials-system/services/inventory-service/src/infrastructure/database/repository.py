"""
SQLAlchemy implementation of the Material Repository.
This is the Infrastructure layer that implements the domain repository interfaces.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.material import (
    Material,
    MaterialUnit,
    StockMovement,
    StockUpdateReason,
    Reservation,
)
from ...domain.repositories.material_repository import (
    MaterialRepository,
    StockMovementRepository,
    ReservationRepository,
)
from .models import MaterialModel, StockMovementModel, ReservationModel


def _model_to_entity(model: MaterialModel) -> Material:
    """Convert SQLAlchemy model to domain entity."""
    return Material(
        id=model.id,
        name=model.name,
        unit=MaterialUnit(model.unit),
        category=model.category or "",
        quantity=model.quantity,
        reserved=model.reserved,
        min_threshold=model.min_threshold,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _entity_to_model(entity: Material) -> MaterialModel:
    """Convert domain entity to SQLAlchemy model."""
    return MaterialModel(
        id=entity.id,
        name=entity.name,
        unit=entity.unit.value,
        category=entity.category,
        quantity=entity.quantity,
        reserved=entity.reserved,
        min_threshold=entity.min_threshold,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


class SQLAlchemyMaterialRepository(MaterialRepository):
    """SQLAlchemy implementation of MaterialRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, material_id: str) -> Optional[Material]:
        result = await self.session.execute(
            select(MaterialModel).where(MaterialModel.id == material_id)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def get_by_name(self, name: str) -> Optional[Material]:
        result = await self.session.execute(
            select(MaterialModel).where(MaterialModel.name == name)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def get_all(
        self,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Material], int]:
        # Build query
        query = select(MaterialModel)
        count_query = select(func.count(MaterialModel.id))

        if category:
            query = query.where(MaterialModel.category == category)
            count_query = count_query.where(MaterialModel.category == category)

        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(MaterialModel.name)

        result = await self.session.execute(query)
        models = result.scalars().all()

        return [_model_to_entity(m) for m in models], total

    async def get_low_stock(self) -> List[Material]:
        # Get materials where available (quantity - reserved) < min_threshold
        result = await self.session.execute(
            select(MaterialModel).where(
                (MaterialModel.quantity - MaterialModel.reserved) < MaterialModel.min_threshold
            )
        )
        models = result.scalars().all()
        return [_model_to_entity(m) for m in models]

    async def save(self, material: Material) -> Material:
        model = _entity_to_model(material)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return _model_to_entity(model)

    async def update(self, material: Material) -> Material:
        result = await self.session.execute(
            select(MaterialModel).where(MaterialModel.id == material.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Material with ID {material.id} not found")

        model.name = material.name
        model.unit = material.unit.value
        model.category = material.category
        model.quantity = material.quantity
        model.reserved = material.reserved
        model.min_threshold = material.min_threshold
        model.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(model)
        return _model_to_entity(model)

    async def delete(self, material_id: str) -> bool:
        result = await self.session.execute(
            select(MaterialModel).where(MaterialModel.id == material_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return False

        await self.session.delete(model)
        await self.session.commit()
        return True

    async def update_quantity(
        self,
        material_id: str,
        delta: int,
        reason: str,
        reference_id: Optional[str] = None
    ) -> Optional[Material]:
        result = await self.session.execute(
            select(MaterialModel).where(MaterialModel.id == material_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None

        model.quantity = max(0, model.quantity + delta)
        model.updated_at = datetime.utcnow()

        # Create stock movement record
        movement = StockMovementModel(
            id=str(uuid.uuid4()),
            material_id=material_id,
            quantity_delta=delta,
            reason=reason,
            reference_id=reference_id,
        )
        self.session.add(movement)

        await self.session.commit()
        await self.session.refresh(model)
        return _model_to_entity(model)

    async def reserve(
        self,
        material_id: str,
        quantity: int,
        request_id: str
    ) -> Optional[str]:
        result = await self.session.execute(
            select(MaterialModel).where(MaterialModel.id == material_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None

        available = model.quantity - model.reserved
        if available < quantity:
            return None

        model.reserved += quantity
        model.updated_at = datetime.utcnow()

        reservation_id = str(uuid.uuid4())
        reservation = ReservationModel(
            id=reservation_id,
            material_id=material_id,
            request_id=request_id,
            quantity=quantity,
            status="ACTIVE",
        )
        self.session.add(reservation)

        await self.session.commit()
        return reservation_id

    async def release_reservation(self, reservation_id: str) -> bool:
        result = await self.session.execute(
            select(ReservationModel).where(ReservationModel.id == reservation_id)
        )
        reservation = result.scalar_one_or_none()
        if not reservation or reservation.status != "ACTIVE":
            return False

        # Get the material and release the reserved quantity
        mat_result = await self.session.execute(
            select(MaterialModel).where(MaterialModel.id == reservation.material_id)
        )
        material = mat_result.scalar_one_or_none()
        if material:
            material.reserved = max(0, material.reserved - reservation.quantity)
            material.updated_at = datetime.utcnow()

        reservation.status = "CANCELLED"

        await self.session.commit()
        return True


class SQLAlchemyStockMovementRepository(StockMovementRepository):
    """SQLAlchemy implementation of StockMovementRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, movement: StockMovement) -> StockMovement:
        model = StockMovementModel(
            id=movement.id,
            material_id=movement.material_id,
            quantity_delta=movement.quantity_delta,
            reason=movement.reason.value if isinstance(movement.reason, StockUpdateReason) else movement.reason,
            reference_id=movement.reference_id,
            notes=movement.notes,
            created_at=movement.created_at,
        )
        self.session.add(model)
        await self.session.commit()
        return movement

    async def get_by_material(
        self,
        material_id: str,
        limit: int = 100
    ) -> List[StockMovement]:
        result = await self.session.execute(
            select(StockMovementModel)
            .where(StockMovementModel.material_id == material_id)
            .order_by(StockMovementModel.created_at.desc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [
            StockMovement(
                id=m.id,
                material_id=m.material_id,
                quantity_delta=m.quantity_delta,
                reason=StockUpdateReason(m.reason) if m.reason in [e.value for e in StockUpdateReason] else m.reason,
                reference_id=m.reference_id,
                notes=m.notes,
                created_at=m.created_at,
            )
            for m in models
        ]

    async def get_by_reference(self, reference_id: str) -> List[StockMovement]:
        result = await self.session.execute(
            select(StockMovementModel)
            .where(StockMovementModel.reference_id == reference_id)
            .order_by(StockMovementModel.created_at.desc())
        )
        models = result.scalars().all()
        return [
            StockMovement(
                id=m.id,
                material_id=m.material_id,
                quantity_delta=m.quantity_delta,
                reason=StockUpdateReason(m.reason) if m.reason in [e.value for e in StockUpdateReason] else m.reason,
                reference_id=m.reference_id,
                notes=m.notes,
                created_at=m.created_at,
            )
            for m in models
        ]


class SQLAlchemyReservationRepository(ReservationRepository):
    """SQLAlchemy implementation of ReservationRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, reservation: Reservation) -> Reservation:
        model = ReservationModel(
            id=reservation.id,
            material_id=reservation.material_id,
            request_id=reservation.request_id,
            quantity=reservation.quantity,
            status=reservation.status,
            created_at=reservation.created_at,
            fulfilled_at=reservation.fulfilled_at,
        )
        self.session.add(model)
        await self.session.commit()
        return reservation

    async def get_by_id(self, reservation_id: str) -> Optional[Reservation]:
        result = await self.session.execute(
            select(ReservationModel).where(ReservationModel.id == reservation_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return Reservation(
            id=model.id,
            material_id=model.material_id,
            request_id=model.request_id,
            quantity=model.quantity,
            status=model.status,
            created_at=model.created_at,
            fulfilled_at=model.fulfilled_at,
        )

    async def get_by_request(self, request_id: str) -> List[Reservation]:
        result = await self.session.execute(
            select(ReservationModel).where(ReservationModel.request_id == request_id)
        )
        models = result.scalars().all()
        return [
            Reservation(
                id=m.id,
                material_id=m.material_id,
                request_id=m.request_id,
                quantity=m.quantity,
                status=m.status,
                created_at=m.created_at,
                fulfilled_at=m.fulfilled_at,
            )
            for m in models
        ]

    async def get_by_material(
        self,
        material_id: str,
        active_only: bool = True
    ) -> List[Reservation]:
        query = select(ReservationModel).where(ReservationModel.material_id == material_id)
        if active_only:
            query = query.where(ReservationModel.status == "ACTIVE")

        result = await self.session.execute(query)
        models = result.scalars().all()
        return [
            Reservation(
                id=m.id,
                material_id=m.material_id,
                request_id=m.request_id,
                quantity=m.quantity,
                status=m.status,
                created_at=m.created_at,
                fulfilled_at=m.fulfilled_at,
            )
            for m in models
        ]

    async def update_status(
        self,
        reservation_id: str,
        status: str
    ) -> Optional[Reservation]:
        result = await self.session.execute(
            select(ReservationModel).where(ReservationModel.id == reservation_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None

        model.status = status
        if status == "FULFILLED":
            model.fulfilled_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(model)

        return Reservation(
            id=model.id,
            material_id=model.material_id,
            request_id=model.request_id,
            quantity=model.quantity,
            status=model.status,
            created_at=model.created_at,
            fulfilled_at=model.fulfilled_at,
        )

    async def cancel(self, reservation_id: str) -> bool:
        result = await self.update_status(reservation_id, "CANCELLED")
        return result is not None
