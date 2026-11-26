"""Data contracts shared across the pipeline.

Every module — loader, extractor, merger — speaks these types only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PageFragment(BaseModel):
    """The exact structured output the LLM must produce for one page.

    ``fields`` holds label/value pairs discovered on the page.
    ``items`` holds table rows (one object per row, header labels as keys);
    leave empty when the page has no table.
    """

    document_title: str = Field(default="", description="Title of the form, e.g. 'Purchase Order'")
    fields: dict[str, str] = Field(default_factory=dict, description="Label -> value pairs, original wording")
    items: list[dict[str, str]] = Field(default_factory=list, description="Table rows; empty when no table present")

    @field_validator("fields")
    @classmethod
    def _drop_empty_values(cls, v: dict[str, str]) -> dict[str, str]:
        return {k.strip(): str(val).strip() for k, val in v.items() if k and str(val).strip()}

    @field_validator("items")
    @classmethod
    def _clean_rows(cls, v: list[dict[str, str]]) -> list[dict[str, str]]:
        return [
            {str(k).strip(): str(val).strip() for k, val in row.items() if str(k).strip()}
            for row in v
        ]


@dataclass(frozen=True)
class PageContent:
    """Raw page payload handed from loaders to the extractor."""

    page_number: int                # 1-based
    kind: Literal["text", "image"]  # 'text': plain text, 'image': raw PNG bytes to OCR
    text: str | None = None
    png_bytes: bytes | None = None

    def __post_init__(self) -> None:
        if self.kind == "text" and not (self.text and self.text.strip()):
            raise ValueError("PageContent of kind 'text' needs non-empty text")
        if self.kind == "image" and not self.png_bytes:
            raise ValueError("PageContent of kind 'image' needs png_bytes")