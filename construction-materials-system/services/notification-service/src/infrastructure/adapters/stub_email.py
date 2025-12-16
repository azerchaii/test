"""
Stub Email Adapter - For testing without real email service.

This adapter simulates email sending for development and testing purposes.
It stores all "sent" emails in memory for verification in tests.
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from ...application.ports.email_adapter import EmailAdapter, EmailResult

logger = logging.getLogger(__name__)


class StubEmailAdapter(EmailAdapter):
    """
    Stub implementation of EmailAdapter for testing.
    
    Features:
    - In-memory storage of all "sent" emails
    - Configurable failure rate for testing error handling
    - Console logging of email contents
    - Search methods for test verification
    
    Usage:
        # Basic usage
        adapter = StubEmailAdapter()
        result = await adapter.send_email(
            to="user@example.com",
            subject="Test",
            body="Hello!"
        )
        
        # Access sent emails for testing
        emails = adapter.get_sent_emails()
        emails_to_user = adapter.find_emails_to("user@example.com")
        adapter.clear()
    """

    def __init__(
        self,
        failure_rate: float = 0.0,
        log_to_console: bool = True,
        simulate_delay: bool = False,
    ):
        """
        Initialize the stub adapter.
        
        Args:
            failure_rate: Probability of send failure (0.0 to 1.0)
            log_to_console: Whether to log emails to console
            simulate_delay: Whether to simulate network delay
        """
        self.failure_rate = failure_rate
        self.log_to_console = log_to_console
        self.simulate_delay = simulate_delay
        
        # In-memory storage
        self._sent_emails: List[Dict[str, Any]] = []

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> EmailResult:
        """
        Simulate sending an email.
        """
        import random
        import asyncio

        # Simulate network delay
        if self.simulate_delay:
            await asyncio.sleep(random.uniform(0.1, 0.5))

        # Simulate random failures
        if random.random() < self.failure_rate:
            self._log_email(to, subject, body, success=False)
            return EmailResult(
                success=False,
                message_id=None,
                error="Simulated email delivery failure",
            )

        # Generate message ID
        message_id = f"STUB-{uuid.uuid4().hex[:12]}"
        
        # Store email
        email_record = {
            "message_id": message_id,
            "to": to,
            "subject": subject,
            "body": body,
            "html_body": html_body,
            "sent_at": datetime.utcnow().isoformat(),
            "status": "SENT",
        }
        self._sent_emails.append(email_record)

        self._log_email(to, subject, body, success=True, message_id=message_id)

        return EmailResult(
            success=True,
            message_id=message_id,
        )

    async def send_bulk(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> List[EmailResult]:
        """
        Send email to multiple recipients.
        """
        results = []
        for recipient in recipients:
            result = await self.send_email(recipient, subject, body, html_body)
            results.append(result)
        return results

    # ==================== Testing Helper Methods ====================

    def get_sent_emails(self) -> List[Dict[str, Any]]:
        """Get all sent emails."""
        return self._sent_emails.copy()

    def find_emails_to(self, recipient: str) -> List[Dict[str, Any]]:
        """Find emails sent to a specific recipient."""
        return [e for e in self._sent_emails if e["to"] == recipient]

    def find_emails_with_subject(self, subject_contains: str) -> List[Dict[str, Any]]:
        """Find emails with subject containing text."""
        return [
            e for e in self._sent_emails 
            if subject_contains.lower() in e["subject"].lower()
        ]

    def get_last_email(self) -> Optional[Dict[str, Any]]:
        """Get the most recently sent email."""
        return self._sent_emails[-1] if self._sent_emails else None

    def get_email_count(self) -> int:
        """Get total number of sent emails."""
        return len(self._sent_emails)

    def clear(self) -> None:
        """Clear all sent emails (for test cleanup)."""
        self._sent_emails.clear()

    def _log_email(
        self,
        to: str,
        subject: str,
        body: str,
        success: bool,
        message_id: Optional[str] = None,
    ) -> None:
        """Log email details to console."""
        if not self.log_to_console:
            return

        status = "SENT" if success else "FAILED"
        border = "=" * 60
        
        log_message = f"""
{border}
[STUB EMAIL] {status}
{border}
Message ID: {message_id or 'N/A'}
To: {to}
Subject: {subject}
{'-' * 60}
{body[:200]}{'...' if len(body) > 200 else ''}
{border}
"""
        if success:
            logger.info(log_message)
        else:
            logger.warning(log_message)
