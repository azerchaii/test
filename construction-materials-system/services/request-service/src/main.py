import os
import logging
import time
from concurrent import futures
import grpc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def serve():
    """Start the gRPC server"""
    grpc_port = os.getenv('GRPC_PORT', '50053')
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add service implementation here when proto files are generated
    # For now, just start the server
    
    server.add_insecure_port(f'[::]:{grpc_port}')
    server.start()
    
    logger.info(f"Request Service started on port {grpc_port}")
    
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        logger.info("Shutting down Request Service...")
        server.stop(0)


if __name__ == '__main__':
    serve()
