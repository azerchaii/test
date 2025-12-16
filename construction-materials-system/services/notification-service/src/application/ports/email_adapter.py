"""
Email Adapter Port - Interface for sending emails.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class EmailResult:
    """Result of sending an email."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailAdapter(ABC):
    """
    Abstract interface for email sending.
    Implementations can be:
    - StubEmailAdapter: For testing without real SMTP
    - SmtpEmailAdapter: For production with actual SMTP server
    """

    @abstractmethod
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> EmailResult:
        """
        Send an email to a single recipient.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            
        Returns:
            EmailResult with success status and message ID
        """
        pass

    @abstractmethod
    async def send_bulk(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> List[EmailResult]:
        """
        Send an email to multiple recipients.
        
        Args:
            recipients: List of email addresses
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            
        Returns:
            List of EmailResults, one per recipient
        """
        pass
