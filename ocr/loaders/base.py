"""Pluggable document loader abstractions.

Design: any loader returns one PageContent per page. New file formats just add a
new DocumentLoader implementation and register it — existing code never changes (OCP).
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from ocr.models import PageContent


@runtime_checkable
class DocumentLoader(Protocol):
    """Load a document into PageContent objects, one per page."""

    def supports(self, path: Path) -> bool: ...

    def load(self, path: Path) -> list[PageContent]: ...


class LoaderRegistry:
    """Maps file extensions to loaders, first match wins."""

    def __init__(self) -> None:
        self._loaders: list[DocumentLoader] = []

    def register(self, loader: DocumentLoader) -> None:
        self._loaders.append(loader)

    def loader_for(self, path: Path) -> DocumentLoader:
        for loader in self._loaders:
            if loader.supports(path):
                return loader
        raise ValueError(
            f"No loader supports '{path}' (extension '{path.suffix}'). "
            "Supported: .pdf, .docx"
        )