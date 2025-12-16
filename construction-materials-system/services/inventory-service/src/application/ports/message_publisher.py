"""
Message Publisher Port - Interface for publishing messages to a message queue.
This is an application-level port that infrastructure adapters will implement.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class MessagePublisher(ABC):
    """
    Abstract interface for publishing messages to a message queue.
    Implementations can use RabbitMQ, Kafka, or any other message broker.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the message broker."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the message broker."""
        pass

    @abstractmethod
    async def publish(
        self,
        exchange: str,
        routing_key: str,
        message: Dict[str, Any],
    ) -> bool:
        """
        Publish a message to the specified exchange with routing key.
        
        Args:
            exchange: The exchange name to publish to
            routing_key: The routing key for the message
            message: The message payload as a dictionary
            
        Returns:
            True if published successfully, False otherwise
        """
        pass

    @abstractmethod
    async def declare_exchange(
        self,
        exchange: str,
        exchange_type: str = "topic",
        durable: bool = True,
    ) -> None:
        """
        Declare an exchange.
        
        Args:
            exchange: The exchange name
            exchange_type: Type of exchange (direct, topic, fanout, headers)
            durable: Whether the exchange survives broker restart
        """
        pass
