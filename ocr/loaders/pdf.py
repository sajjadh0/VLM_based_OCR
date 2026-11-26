"""PDF page loading: text layer when present, OCR-rendered image otherwise."""

from __future__ import annotations

from pathlib import Path

import pymupdf as fitz  # PyMuPDF

from ocr.loaders.base import DocumentLoader
from ocr.models import PageContent


class PdfLoader:
    """One PDF -> one PageContent per page (text if embedded, image otherwise)."""

    SUPPORTED_SUFFIXES = {".pdf"}
    MIN_TEXT_CHARS = 50  # below this, treat page as image-only / scanned

    def __init__(self, dpi: int = 300) -> None:
        self.dpi = dpi

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_SUFFIXES

    def load(self, path: Path) -> list[PageContent]:
        pages: list[PageContent] = []
        with fitz.open(path) as doc:
            for idx, page in enumerate(doc, start=1):
                text = page.get_text("text")
                if len(text.strip()) >= self.MIN_TEXT_CHARS:
                    pages.append(PageContent(page_number=idx, kind="text", text=text))
                    continue
                pix = page.get_pixmap(dpi=self.dpi)
                pages.append(
                    PageContent(page_number=idx, kind="image", png_bytes=pix.tobytes("png"))
                )
        return pages
