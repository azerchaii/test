"""
gRPC Server implementation for Inventory Service.
"""
import logging
from typing import Optional

import grpc
from grpc import aio

from ...application.use_cases.material_use_cases import (
    CreateMaterialUseCase,
    GetMaterialUseCase,
    ListMaterialsUseCase,
    UpdateMaterialUseCase,
    CheckAvailabilityUseCase,
    ReserveMaterialUseCase,
    ReleaseReservationUseCase,
    UpdateStockUseCase,
    GetLowStockMaterialsUseCase,
)
from ...application.dto.material_dto import (
    CreateMaterialDTO,
    UpdateMaterialDTO,
    ListMaterialsDTO,
    AvailabilityCheckDTO,
    ReserveMaterialDTO,
    UpdateStockDTO,
)
from ...domain.repositories.material_repository import MaterialRepository
from ...application.ports.message_publisher import MessagePublisher

# Import generated protobuf modules (will be generated from proto files)
# For now, we'll create a simplified version
logger = logging.getLogger(__name__)


class InventoryServicer:
    """gRPC servicer for Inventory Service."""

    def __init__(
        self,
        material_repo: MaterialRepository,
        message_publisher: Optional[MessagePublisher] = None,
    ):
        self.material_repo = material_repo
        self.message_publisher = message_publisher
        
        # Initialize use cases
        self.create_material_uc = CreateMaterialUseCase(material_repo)
        self.get_material_uc = GetMaterialUseCase(material_repo)
        self.list_materials_uc = ListMaterialsUseCase(material_repo)
        self.update_material_uc = UpdateMaterialUseCase(material_repo)
        self.check_availability_uc = CheckAvailabilityUseCase(material_repo, message_publisher)
        self.reserve_material_uc = ReserveMaterialUseCase(material_repo)
        self.release_reservation_uc = ReleaseReservationUseCase(material_repo)
        self.update_stock_uc = UpdateStockUseCase(material_repo, message_publisher)
        self.get_low_stock_uc = GetLowStockMaterialsUseCase(material_repo)

    async def GetMaterial(self, request, context):
        """Get a material by ID."""
        try:
            result = await self.get_material_uc.execute(request.material_id)
            if not result:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Material {request.material_id} not found")
                return None
            
            return self._material_dto_to_response(result)
        except Exception as e:
            logger.error(f"Error in GetMaterial: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return None

    async def ListMaterials(self, request, context):
        """List materials with pagination."""
        try:
            dto = ListMaterialsDTO(
                category=request.category if request.category else None,
                page=request.page or 1,
                page_size=request.page_size or 20,
            )
            result = await self.list_materials_uc.execute(dto)
            
            # Build response (simplified - actual implementation uses generated protobuf)
            return {
                "materials": [self._material_dto_to_dict(m) for m in result.materials],
                "total_count": result.total_count,
                "page": result.page,
                "page_size": result.page_size,
            }
        except Exception as e:
            logger.error(f"Error in ListMaterials: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return None

    async def CreateMaterial(self, request, context):
        """Create a new material."""
        try:
            dto = CreateMaterialDTO(
                name=request.name,
                unit=request.unit,
                category=request.category,
                initial_quantity=request.initial_quantity,
                min_threshold=request.min_threshold,
            )
            result = await self.create_material_uc.execute(dto)
            return self._material_dto_to_response(result)
        except ValueError as e:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(str(e))
            return None
        except Exception as e:
            logger.error(f"Error in CreateMaterial: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return None

    async def UpdateMaterial(self, request, context):
        """Update a material."""
        try:
            dto = UpdateMaterialDTO(
                material_id=request.material_id,
                name=request.name if request.name else None,
                unit=request.unit if request.unit else None,
                category=request.category if request.category else None,
                min_threshold=request.min_threshold if request.min_threshold else None,
            )
            result = await self.update_material_uc.execute(dto)
            if not result:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Material {request.material_id} not found")
                return None
            return self._material_dto_to_response(result)
        except Exception as e:
            logger.error(f"Error in UpdateMaterial: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return None

    async def CheckAvailability(self, request, context):
        """Check material availability."""
        try:
            dto = AvailabilityCheckDTO(
                material_id=request.material_id,
                requested_quantity=request.requested_quantity,
            )
            result = await self.check_availability_uc.execute(dto)
            
            return {
                "is_available": result.is_available,
                "available_quantity": result.available_quantity,
                "requested_quantity": result.requested_quantity,
                "shortage": result.shortage,
                "material_id": result.material_id,
                "material_name": result.material_name,
            }
        except ValueError as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return None
        except Exception as e:
            logger.error(f"Error in CheckAvailability: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return None

    async def ReserveMaterial(self, request, context):
        """Reserve material for a request."""
        try:
            dto = ReserveMaterialDTO(
                material_id=request.material_id,
                quantity=request.quantity,
                request_id=request.request_id,
            )
            result = await self.reserve_material_uc.execute(dto)
            
            return {
                "success": result.success,
                "reservation_id": result.reservation_id or "",
                "reserved_quantity": result.reserved_quantity,
                "error_message": result.error_message or "",
            }
        except Exception as e:
            logger.error(f"Error in ReserveMaterial: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return None

    async def ReleaseReservation(self, request, context):
        """Release a reservation."""
        try:
            success = await self.release_reservation_uc.execute(request.reservation_id)
            return {
                "success": success,
                "error_message": "" if success else "Reservation not found or already released",
            }
        except Exception as e:
            logger.error(f"Error in ReleaseReservation: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return None

    async def UpdateStock(self, request, context):
        """Update stock quantity."""
        try:
            dto = UpdateStockDTO(
                material_id=request.material_id,
                quantity_delta=request.quantity_delta,
                reason=request.reason,
                reference_id=request.reference_id if request.reference_id else None,
            )
            result = await self.update_stock_uc.execute(dto)
            
            return {
                "success": result.success,
                "new_quantity": result.new_quantity,
                "error_message": result.error_message or "",
            }
        except Exception as e:
            logger.error(f"Error in UpdateStock: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return None

    async def GetLowStockMaterials(self, request, context):
        """Get materials below threshold."""
        try:
            result = await self.get_low_stock_uc.execute()
            return {
                "materials": [self._material_dto_to_dict(m) for m in result],
            }
        except Exception as e:
            logger.error(f"Error in GetLowStockMaterials: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return None

    def _material_dto_to_response(self, dto):
        """Convert MaterialDTO to gRPC response."""
        return self._material_dto_to_dict(dto)

    def _material_dto_to_dict(self, dto):
        """Convert MaterialDTO to dictionary."""
        return {
            "id": dto.id,
            "name": dto.name,
            "unit": dto.unit,
            "category": dto.category,
            "quantity": dto.quantity,
            "reserved": dto.reserved,
            "available": dto.available,
            "min_threshold": dto.min_threshold,
            "created_at": dto.created_at,
            "updated_at": dto.updated_at,
        }


async def serve(
    port: int,
    material_repo: MaterialRepository,
    message_publisher: Optional[MessagePublisher] = None,
) -> aio.Server:
    """Start the gRPC server."""
    server = aio.server()
    
    servicer = InventoryServicer(material_repo, message_publisher)
    
    # Note: In production, you would add the generated servicer here:
    # inventory_pb2_grpc.add_InventoryServiceServicer_to_server(servicer, server)
    
    server.add_insecure_port(f"[::]:{port}")
    
    logger.info(f"Starting gRPC server on port {port}")
    await server.start()
    
    return server
