"""
Main entry point for Inventory Service.
"""
import asyncio
import logging
import os
import signal
from typing import Optional

from .infrastructure.database.connection import Database, init_database
from .infrastructure.database.repository import SQLAlchemyMaterialRepository
from .infrastructure.message_queue.rabbitmq_publisher import (
    RabbitMQPublisher,
    StubMessagePublisher,
)
from .infrastructure.grpc_server.server import serve, InventoryServicer

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Config:
    """Service configuration from environment variables."""
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/inventory.db")
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://admin:admin123@localhost:5672/")
    GRPC_PORT: int = int(os.getenv("GRPC_PORT", "50051"))
    USE_STUBS: bool = os.getenv("USE_STUBS", "true").lower() == "true"


async def seed_initial_data(db: Database) -> None:
    """Seed initial data for testing."""
    from .domain.entities.material import Material, MaterialUnit
    import uuid
    
    async with db.session() as session:
        repo = SQLAlchemyMaterialRepository(session)
        
        # Check if data already exists
        materials, count = await repo.get_all(page=1, page_size=1)
        if count > 0:
            logger.info("Data already exists, skipping seed")
            return
        
        # Sample materials for construction
        sample_materials = [
            Material(
                id=str(uuid.uuid4()),
                name="Балка стальная 200x100",
                unit=MaterialUnit.PIECES,
                category="Металлоконструкции",
                quantity=50,
                min_threshold=10,
            ),
            Material(
                id=str(uuid.uuid4()),
                name="Цемент М500",
                unit=MaterialUnit.KILOGRAMS,
                category="Сыпучие материалы",
                quantity=5000,
                min_threshold=1000,
            ),
            Material(
                id=str(uuid.uuid4()),
                name="Кирпич красный",
                unit=MaterialUnit.PIECES,
                category="Кирпич",
                quantity=10000,
                min_threshold=2000,
            ),
            Material(
                id=str(uuid.uuid4()),
                name="Арматура 12мм",
                unit=MaterialUnit.METERS,
                category="Металлоконструкции",
                quantity=500,
                min_threshold=100,
            ),
            Material(
                id=str(uuid.uuid4()),
                name="Песок строительный",
                unit=MaterialUnit.CUBIC_METERS,
                category="Сыпучие материалы",
                quantity=100,
                min_threshold=20,
            ),
            Material(
                id=str(uuid.uuid4()),
                name="Доска обрезная 50x150",
                unit=MaterialUnit.CUBIC_METERS,
                category="Пиломатериалы",
                quantity=30,
                min_threshold=5,
            ),
        ]
        
        for material in sample_materials:
            await repo.save(material)
        
        logger.info(f"Seeded {len(sample_materials)} materials")


async def main() -> None:
    """Main entry point."""
    logger.info("Starting Inventory Service...")
    logger.info(f"Database URL: {Config.DATABASE_URL}")
    logger.info(f"gRPC Port: {Config.GRPC_PORT}")
    logger.info(f"Use Stubs: {Config.USE_STUBS}")
    
    # Initialize database
    db = init_database(Config.DATABASE_URL)
    await db.create_tables()
    logger.info("Database tables created")
    
    # Seed initial data
    await seed_initial_data(db)
    
    # Initialize message publisher
    message_publisher: Optional[RabbitMQPublisher | StubMessagePublisher] = None
    if Config.USE_STUBS:
        message_publisher = StubMessagePublisher()
        await message_publisher.connect()
    else:
        try:
            message_publisher = RabbitMQPublisher(Config.RABBITMQ_URL)
            await message_publisher.connect()
        except Exception as e:
            logger.warning(f"Failed to connect to RabbitMQ: {e}. Using stub publisher.")
            message_publisher = StubMessagePublisher()
            await message_publisher.connect()
    
    # Create repository and start gRPC server
    async with db.session() as session:
        material_repo = SQLAlchemyMaterialRepository(session)
        
        # Start gRPC server
        server = await serve(
            port=Config.GRPC_PORT,
            material_repo=material_repo,
            message_publisher=message_publisher,
        )
        
        logger.info(f"Inventory Service started on port {Config.GRPC_PORT}")
        
        # Handle graceful shutdown
        stop_event = asyncio.Event()
        
        def handle_signal(sig):
            logger.info(f"Received signal {sig}, shutting down...")
            stop_event.set()
        
        for sig in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_event_loop().add_signal_handler(
                sig, lambda s=sig: handle_signal(s)
            )
        
        # Wait for shutdown signal
        await stop_event.wait()
        
        # Cleanup
        logger.info("Shutting down gRPC server...")
        await server.stop(grace=5)
        
        if message_publisher:
            await message_publisher.disconnect()
        
        await db.close()
        logger.info("Inventory Service stopped")


if __name__ == "__main__":
    asyncio.run(main())
