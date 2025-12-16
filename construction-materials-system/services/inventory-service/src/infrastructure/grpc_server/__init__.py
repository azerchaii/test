"""gRPC Server infrastructure."""
from .server import InventoryServicer, serve

__all__ = ["InventoryServicer", "serve"]
