"""API client for VodaCare chatbot."""
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class VodaCareAPIError(Exception):
    """Exception raised for API errors."""
    pass


class VodaCareClient:
    """Client for interacting with the VodaCare chatbot API."""

    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the API client.

        Args:
            base_url: Base URL for the API (e.g., http://localhost:8000)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()

    def send_message(
        self,
        message: str,
        session_id: str,
        participant_group: str = "A",
        participant_id: str = None
    ) -> Dict[str, Any]:
        """
        Send a message to the chatbot and get response.
        Also stores messages to database.

        Args:
            message: User message text
            session_id: Unique session identifier for the conversation
            participant_group: Variant group ("A" or "B")
            participant_id: Optional participant identifier

        Returns:
            Dict containing:
                - response: Assistant's response text
                - latency_ms: Response time in milliseconds
                - timestamp: When the response was received

        Raises:
            VodaCareAPIError: If the API request fails
        """
        url = f"{self.base_url}/api/chat"

        payload = {
            "message": message,
            "session_id": session_id,
            "participant_group": participant_group
        }

        try:
            start_time = datetime.now()

            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout
            )

            end_time = datetime.now()
            latency_ms = (end_time - start_time).total_seconds() * 1000

            response.raise_for_status()

            data = response.json()
            assistant_reply = data.get("reply", "")

            # Store user message to database
            self._store_message(
                session_id=session_id,
                role="user",
                content=message,
                participant_id=participant_id,
                participant_group=participant_group
            )

            # Store assistant response to database
            self._store_message(
                session_id=session_id,
                role="assistant",
                content=assistant_reply,
                participant_id=participant_id,
                participant_group=participant_group
            )

            return {
                "response": assistant_reply,
                "latency_ms": latency_ms,
                "timestamp": end_time,
                "raw_response": data
            }

        except requests.exceptions.Timeout:
            logger.error(f"Request timed out after {self.timeout}s")
            raise VodaCareAPIError(
                f"Request timed out after {self.timeout} seconds"
            )

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise VodaCareAPIError(
                f"Failed to connect to API at {url}. "
                f"Is the server running?"
            )

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise VodaCareAPIError(
                f"API returned error status {response.status_code}: "
                f"{response.text}"
            )

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise VodaCareAPIError(f"Unexpected error: {e}")

    def _store_message(
        self,
        session_id: str,
        role: str,
        content: str,
        participant_id: Optional[str] = None,
        participant_group: Optional[str] = None
    ):
        """
        Store a message to the database via /api/messages endpoint.

        Args:
            session_id: Session identifier
            role: "user" or "assistant"
            content: Message content
            participant_id: Optional participant ID
            participant_group: Optional participant group
        """
        url = f"{self.base_url}/api/messages"

        payload = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "participant_id": participant_id,
            "participant_group": participant_group
        }

        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=5
            )

            if response.status_code >= 400:
                logger.warning(
                    f"Failed to store {role} message to DB: {response.status_code}"
                )
        except Exception as e:
            # Non-fatal - log but don't fail the conversation
            logger.warning(f"Error storing message to DB: {e}")

    def register_participant(
        self,
        participant_id: str,
        session_id: str,
        group: str,
        name: Optional[str] = None
    ):
        """
        Register a participant in the database.

        Args:
            participant_id: Unique participant identifier
            session_id: Session identifier
            group: Participant group ("A" or "B")
            name: Optional participant name
        """
        url = f"{self.base_url}/api/participants"

        payload = {
            "participant_id": participant_id,
            "session_id": session_id,
            "group": group,
            "name": name
        }

        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=5
            )

            if response.status_code >= 400:
                logger.warning(
                    f"Failed to register participant: {response.status_code}"
                )
        except Exception as e:
            logger.warning(f"Error registering participant: {e}")

    def health_check(self) -> bool:
        """
        Check if the API is accessible.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # Try a simple GET to the root or health endpoint
            url = f"{self.base_url}/health"
            response = self.session.get(url, timeout=5)

            if response.status_code == 200:
                return True

        except requests.exceptions.RequestException:
            pass

        # If /health doesn't exist, try root
        try:
            url = self.base_url
            response = self.session.get(url, timeout=5)
            return response.status_code < 500

        except requests.exceptions.RequestException:
            return False

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
