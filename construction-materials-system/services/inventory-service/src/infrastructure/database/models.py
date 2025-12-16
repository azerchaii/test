"""
SQLAlchemy models for Inventory Service.
These are the database table definitions.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class MaterialModel(Base):
    """SQLAlchemy model for materials table."""
    
    __tablename__ = "materials"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    unit = Column(String, nullable=False)
    category = Column(String)
    quantity = Column(Integer, default=0)
    reserved = Column(Integer, default=0)
    min_threshold = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    stock_movements = relationship("StockMovementModel", back_populates="material")
    reservations = relationship("ReservationModel", back_populates="material")

    __table_args__ = (
        Index("idx_materials_category", "category"),
        Index("idx_materials_name", "name"),
    )


class StockMovementModel(Base):
    """SQLAlchemy model for stock movements (audit trail)."""
    
    __tablename__ = "stock_movements"

    id = Column(String, primary_key=True)
    material_id = Column(String, ForeignKey("materials.id"), nullable=False)
    quantity_delta = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)  # PURCHASE, MANUAL_ADJUSTMENT, CONSUMPTION, etc.
    reference_id = Column(String)  # order_id, request_id, etc.
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    material = relationship("MaterialModel", back_populates="stock_movements")

    __table_args__ = (
        Index("idx_movements_material", "material_id"),
        Index("idx_movements_reference", "reference_id"),
        Index("idx_movements_created", "created_at"),
    )


class ReservationModel(Base):
    """SQLAlchemy model for material reservations."""
    
    __tablename__ = "reservations"

    id = Column(String, primary_key=True)
    material_id = Column(String, ForeignKey("materials.id"), nullable=False)
    request_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String, default="ACTIVE")  # ACTIVE, FULFILLED, CANCELLED
    created_at = Column(DateTime, default=datetime.utcnow)
    fulfilled_at = Column(DateTime)

    # Relationships
    material = relationship("MaterialModel", back_populates="reservations")

    __table_args__ = (
        Index("idx_reservations_material", "material_id"),
        Index("idx_reservations_request", "request_id"),
        Index("idx_reservations_status", "status"),
    )
