import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class VodaCareAPIError(Exception):
    pass


class VodaCareClient:

    def __init__(self, base_url: str, timeout: int = 30):
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
        url = f"{self.base_url}/api/chat"
        payload = {
            "message": message,
            "session_id": session_id,
            "participant_group": participant_group
        }

        try:
            start_time = datetime.now()
            response = self.session.post(url, json=payload, timeout=self.timeout)
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            response.raise_for_status()

            data = response.json()
            assistant_reply = data.get("reply", "")

            self._store_message(session_id, "user", message, participant_id, participant_group)
            self._store_message(session_id, "assistant", assistant_reply, participant_id, participant_group)

            return {
                "response": assistant_reply,
                "latency_ms": latency_ms,
                "timestamp": datetime.now(),
                "raw_response": data
            }

        except requests.exceptions.Timeout:
            raise VodaCareAPIError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise VodaCareAPIError(f"Failed to connect to API at {url}. Is the server running?")
        except requests.exceptions.HTTPError as e:
            raise VodaCareAPIError(f"API returned error status {response.status_code}: {response.text}")
        except Exception as e:
            raise VodaCareAPIError(f"Unexpected error: {e}")

    def _store_message(
        self,
        session_id: str,
        role: str,
        content: str,
        participant_id: Optional[str] = None,
        participant_group: Optional[str] = None
    ):
        url = f"{self.base_url}/api/messages"
        payload = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "participant_id": participant_id,
            "participant_group": participant_group
        }
        try:
            response = self.session.post(url, json=payload, timeout=5)
            if response.status_code >= 400:
                logger.warning(f"Failed to store {role} message: {response.status_code}")
        except Exception as e:
            # Non-fatal — don't let a storage failure abort the conversation
            logger.warning(f"Error storing message: {e}")

    def register_participant(
        self,
        participant_id: str,
        session_id: str,
        group: str,
        name: Optional[str] = None
    ):
        url = f"{self.base_url}/api/participants"
        payload = {"participant_id": participant_id, "session_id": session_id, "group": group, "name": name}
        try:
            response = self.session.post(url, json=payload, timeout=5)
            if response.status_code >= 400:
                logger.warning(f"Failed to register participant: {response.status_code}")
        except Exception as e:
            logger.warning(f"Error registering participant: {e}")

    def health_check(self) -> bool:
        for url in [f"{self.base_url}/health", self.base_url]:
            try:
                response = self.session.get(url, timeout=5)
                if response.status_code < 500:
                    return True
            except requests.exceptions.RequestException:
                continue
        return False

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
