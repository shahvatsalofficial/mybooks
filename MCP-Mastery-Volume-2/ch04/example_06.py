"""
Universal API Pagination Normalizer for Model Context Protocol
Author: Vatsal Shah | Vatsal Shah
Runtime: Python 3.11+
"""

import base64
import json
import re
from typing import Dict, Any, List, Optional, Tuple

class PaginationNormalizer:
    """Normalizes heterogeneous API pagination models into canonical MCP iterators."""

    @staticmethod
    def encode_cursor(cursor_data: Dict[str, Any]) -> str:
        """Serialize pagination state dictionary to URL-safe base64 string."""
        serialized = json.dumps(cursor_data, sort_keys=True)
        return base64.urlsafe_b64encode(serialized.encode("utf-8")).decode("utf-8")

    @staticmethod
    def decode_cursor(opaque_token: Optional[str]) -> Dict[str, Any]:
        """Deserialize opaque token back to pagination parameters."""
        if not opaque_token:
            return {}
        try:
            decoded_bytes = base64.urlsafe_b64decode(opaque_token.encode("utf-8"))
            return json.loads(decoded_bytes.decode("utf-8"))
        except Exception:
            return {}

    @classmethod
    def normalize_response(
        cls,
        upstream_json: Dict[str, Any],
        http_headers: Optional[Dict[str, str]] = None,
        default_items_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inspect upstream JSON body and headers to produce canonical MCP envelope.
        """
        # 1. Identify Items List
        items: List[Any] = []
        if default_items_key and default_items_key in upstream_json:
            items = upstream_json[default_items_key]
        else:
            for candidate in ("data", "items", "results", "records", "nodes"):
                if candidate in upstream_json and isinstance(upstream_json[candidate], list):
                    items = upstream_json[candidate]
                    break

        has_more = False
        next_cursor = None
        total_count = upstream_json.get("total") or upstream_json.get("total_count")

        # 2. Check Opaque Cursor Patterns (Stripe / Slack style)
        if "has_more" in upstream_json:
            has_more = bool(upstream_json["has_more"])
            if has_more and "next_cursor" in upstream_json:
                next_cursor = cls.encode_cursor({"cursor": upstream_json["next_cursor"]})
            elif has_more and items and isinstance(items[-1], dict) and "id" in items[-1]:
                next_cursor = cls.encode_cursor({"starting_after": items[-1]["id"]})

        # 3. Check Offset / Page Patterns
        elif "page" in upstream_json and "total_pages" in upstream_json:
            current_page = int(upstream_json["page"])
            total_pages = int(upstream_json["total_pages"])
            if current_page < total_pages:
                has_more = True
                next_cursor = cls.encode_cursor({"page": current_page + 1})

        # 4. Check RFC 5988 Link Header Patterns (GitHub style)
        elif http_headers and "link" in http_headers:
            link_header = http_headers["link"]
            match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
            if match:
                has_more = True
                next_cursor = cls.encode_cursor({"next_url": match.group(1)})

        return {
            "status": "success",
            "count": len(items),
            "items": items,
            "pagination": {
                "has_more": has_more,
                "next_cursor": next_cursor,
                "total_count": total_count
            }
        }
