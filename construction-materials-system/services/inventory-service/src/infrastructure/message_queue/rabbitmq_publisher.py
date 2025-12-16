"""
RabbitMQ implementation of MessagePublisher.
"""
import json
import logging
from typing import Any, Dict, Optional

import aio_pika
from aio_pika import ExchangeType, DeliveryMode

from ...application.ports.message_publisher import MessagePublisher

logger = logging.getLogger(__name__)


class RabbitMQPublisher(MessagePublisher):
    """RabbitMQ implementation of the MessagePublisher interface."""

    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self._exchanges: Dict[str, aio_pika.Exchange] = {}

    async def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        try:
            self.connection = await aio_pika.connect_robust(self.connection_url)
            self.channel = await self.connection.channel()
            logger.info("Connected to RabbitMQ")
            
            # Declare default exchanges
            await self.declare_exchange("materials.events", "topic")
            await self.declare_exchange("orders.events", "topic")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection to RabbitMQ."""
        if self.connection:
            await self.connection.close()
            self.connection = None
            self.channel = None
            self._exchanges.clear()
            logger.info("Disconnected from RabbitMQ")

    async def declare_exchange(
        self,
        exchange: str,
        exchange_type: str = "topic",
        durable: bool = True,
    ) -> None:
        """Declare an exchange."""
        if not self.channel:
            raise RuntimeError("Not connected to RabbitMQ")

        type_map = {
            "topic": ExchangeType.TOPIC,
            "direct": ExchangeType.DIRECT,
            "fanout": ExchangeType.FANOUT,
            "headers": ExchangeType.HEADERS,
        }

        exchange_obj = await self.channel.declare_exchange(
            exchange,
            type_map.get(exchange_type, ExchangeType.TOPIC),
            durable=durable,
        )
        self._exchanges[exchange] = exchange_obj
        logger.debug(f"Declared exchange: {exchange}")

    async def publish(
        self,
        exchange: str,
        routing_key: str,
        message: Dict[str, Any],
    ) -> bool:
        """Publish a message to the specified exchange."""
        if not self.channel:
            logger.error("Not connected to RabbitMQ")
            return False

        try:
            # Get or declare exchange
            if exchange not in self._exchanges:
                await self.declare_exchange(exchange)

            exchange_obj = self._exchanges[exchange]

            # Create message
            msg = aio_pika.Message(
                body=json.dumps(message, default=str).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
            )

            # Publish
            await exchange_obj.publish(msg, routing_key=routing_key)
            logger.info(f"Published message to {exchange}/{routing_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False


class StubMessagePublisher(MessagePublisher):
    """
    Stub implementation of MessagePublisher for testing.
    Stores messages in memory instead of sending to RabbitMQ.
    """

    def __init__(self):
        self.messages: list = []
        self.connected = False

    async def connect(self) -> None:
        """Simulate connection."""
        self.connected = True
        logger.info("[STUB] Connected to message queue")

    async def disconnect(self) -> None:
        """Simulate disconnection."""
        self.connected = False
        logger.info("[STUB] Disconnected from message queue")

    async def declare_exchange(
        self,
        exchange: str,
        exchange_type: str = "topic",
        durable: bool = True,
    ) -> None:
        """Simulate exchange declaration."""
        logger.debug(f"[STUB] Declared exchange: {exchange}")

    async def publish(
        self,
        exchange: str,
        routing_key: str,
        message: Dict[str, Any],
    ) -> bool:
        """Store message in memory."""
        self.messages.append({
            "exchange": exchange,
            "routing_key": routing_key,
            "message": message,
        })
        logger.info(f"[STUB] Published message to {exchange}/{routing_key}: {message}")
        return True

    def get_messages(self) -> list:
        """Get all published messages (for testing)."""
        return self.messages

    def clear(self) -> None:
        """Clear all messages (for testing)."""
        self.messages.clear()
