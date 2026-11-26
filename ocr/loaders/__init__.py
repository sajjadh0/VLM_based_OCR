"""Loader registry and built‑in loaders.

Provides ``default_registry()`` with PDF and Word loaders pre‑registered;
custom formats can be added by registering another ``DocumentLoader``.
"""

from ocr.loaders.base import LoaderRegistry, DocumentLoader
from ocr.loaders.pdf import PdfLoader
from ocr.loaders.word import WordLoader


def default_registry() -> LoaderRegistry:
    registry = LoaderRegistry()
    registry.register(PdfLoader())
    registry.register(WordLoader())
    return registry


__all__ = ["LoaderRegistry", "DocumentLoader", "default_registry"]