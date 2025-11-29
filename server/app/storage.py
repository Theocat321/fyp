from __future__ import annotations

import json
from typing import List, Dict, Tuple
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

    def insert_rows(self, table: str, rows: List[Dict], upsert: bool = False) -> Tuple[int, int]:
        """Insert or upsert rows via Supabase REST. Returns (stored, status_code)."""
        if not self.is_configured():
            return 0, 202
        endpoint = f"{self.url}/rest/v1/{table}"
        resp = requests.post(endpoint, headers=self._headers(upsert=upsert), data=json.dumps(rows), timeout=10)
        if 200 <= resp.status_code < 300:
            return len(rows), resp.status_code
        return 0, resp.status_code

