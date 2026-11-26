"""Load .docx documents into page-like units (single unit for simplicity)."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from docx import Document  # python-docx

from ocr.loaders.base import DocumentLoader
from ocr.models import PageContent


class WordLoader:
    """One DOCX -> one PageContent (combined paragraphs + tables).

    ``.doc`` (pre-OOXML) is not supported. Users are directed to convert first.
    """

    SUPPORTED_SUFFIXES = {".docx"}

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_SUFFIXES

    def load(self, path: Path) -> list[PageContent]:
        if path.suffix.lower() == ".doc":
            raise ValueError(
                f"File '{path}' has .doc extension (pre-OOXML). "
                "Please save as .docx (or convert using LibreOffice / Word)."
            )
        doc = Document(path)
        # Flatten all paragraphs + table rows into a single text block.
        lines: list[str] = []
        for para in doc.paragraphs:
            lines.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    # avoid empty cells
                    lines.append(cell.text.strip() if cell.text else "")
        text = "\n".join(lines).strip()
        if not text:
            # Very rarely a completely empty doc; treat as image? Not needed here.
            text = ""
        return [PageContent(page_number=1, kind="text", text=text)]