from __future__ import annotations

import json
from typing import List, Dict, Tuple, Optional
import requests

from .config import get_supabase_url, get_supabase_service_key


class SupabaseStore:
    def __init__(self) -> None:
        self.url = get_supabase_url()
        self.key = get_supabase_service_key()

    def is_configured(self) -> bool:
        return bool(self.url and self.key)

    def _headers(self, upsert: bool = False) -> Dict[str, str]:
        h = {
            "apikey": self.key or "",
            "Authorization": f"Bearer {self.key}" if self.key else "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if upsert:
            h["Prefer"] = "resolution=merge-duplicates,return=minimal"
        else:
            h["Prefer"] = "return=minimal"
        return h

    def insert_rows(
        self,
        table: str,
        rows: List[Dict],
        upsert: bool = False,
        on_conflict: Optional[str] = None,
    ) -> Tuple[int, int]:
        """Insert or upsert rows via Supabase REST. Returns (stored, status_code)."""
        if not self.is_configured():
            return 0, 202
        endpoint = f"{self.url}/rest/v1/{table}"
        if upsert and on_conflict:
            endpoint += f"?on_conflict={on_conflict}"
        resp = requests.post(endpoint, headers=self._headers(upsert=upsert), data=json.dumps(rows), timeout=10)
        if 200 <= resp.status_code < 300:
            return len(rows), resp.status_code
        # Treat conflicts (e.g., duplicate inserts) as non-fatal/no-op
        if resp.status_code == 409:
            return 0, 200
        try:
            # Log brief error context to aid debugging
            from logging import getLogger

            logger = getLogger(__name__)
            msg = resp.text[:500] if resp.text else ""
            logger.warning(
                "Supabase insert failed: table=%s status=%s response=%s", table, resp.status_code, msg
            )
        except Exception:
            pass
        return 0, resp.status_code

    def update_by_pk(
        self,
        table: str,
        pk_col: str,
        pk_value: str,
        fields: Dict,
    ) -> Tuple[int, int]:
        """Patch a single row by primary key column using PostgREST eq filter."""
        if not self.is_configured():
            return 0, 202
        endpoint = f"{self.url}/rest/v1/{table}?{pk_col}=eq.{pk_value}"
        resp = requests.patch(endpoint, headers=self._headers(upsert=False), data=json.dumps(fields), timeout=10)
        if 200 <= resp.status_code < 300:
            # PostgREST returns 204 No Content by default; treat as updated 1
            return 1, resp.status_code
        try:
            from logging import getLogger

            logger = getLogger(__name__)
            msg = resp.text[:500] if resp.text else ""
            logger.warning(
                "Supabase update failed: table=%s status=%s response=%s", table, resp.status_code, msg
            )
        except Exception:
            pass
        return 0, resp.status_code
