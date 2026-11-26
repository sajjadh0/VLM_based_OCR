"""Merge per-page PageFragment objects into the final JSON structure.

Rules:
- One top‑level JSON object: ``{"<Title>": {"fields": {...}, "items": [...]}}``
- ``document_title``: first non‑empty title wins; fallback is the file stem.
- ``fields``: merged dict. If the same key appears on multiple pages, later
  pages get suffix ``_<page_number>`` (e.g. ``Date_p2``).
- ``items``: concatenated array across all pages.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from ocr.models import PageFragment


class Merger:
    def __init__(self, document_name: str) -> None:
        self._document_name = document_name
        self._fields: Dict[str, str] = {}
        self._seen_keys: Dict[str, int] = {}  # key -> first page it appeared on (1‑based)
        self._items: List[Dict[str, str]] = []
        self._document_title: str | None = None

    def add_page(self, fragment: PageFragment, page_num: int) -> None:
        # Title: first non‑empty wins
        if fragment.document_title.strip():
            if not self._document_title:
                self._document_title = fragment.document_title.strip()

        # Merge fields, dedup with page suffixes
        for key, value in fragment.fields.items():
            if key not in self._seen_keys:
                self._seen_keys[key] = page_num
                self._fields[key] = value
            else:
                self._fields[f"{key}_p{page_num}"] = value

        # Merge items
        self._items.extend(fragment.items)

    def finalize(self) -> Dict[str, Dict[str, Any]]:
        document_title = self._document_title if self._document_title else Path(self._document_name).stem
        return {
            document_title: {
                "fields": self._fields,
                "items": self._items,
            }
        }