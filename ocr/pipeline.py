"""Top-level orchestrator: load PDF/DOCX -> extract each page -> merge final JSON."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from ocr.loaders import default_registry
from ocr.extractor import PageExtractor
from ocr.models import PageContent
from ocr.merger import Merger
from ocr.settings import Settings


class PipelineError(Exception):
    pass


def process_file(file_path: str | Path, settings: Settings) -> Dict[str, Dict[str, Any]]:
    """Process a file (PDF or DOCX) and return the final JSON dict.

    Raises ``PipelineError`` if no pages could be extracted.
    """
    registry = default_registry()
    loader = registry.loader_for(Path(file_path))
    pages: list[PageContent] = loader.load(Path(file_path))

    extractor = PageExtractor(settings)
    extractor.set_total_pages(len(pages))

    merger = Merger(document_name=Path(file_path).name)
    succeeded = 0
    for idx, page in enumerate(pages, start=1):
        try:
            fragment = extractor.extract(page)
            succeeded += 1
        except Exception as e:
            print(f"[WARN] Skipping page {idx}: {e}")
            continue
        merger.add_page(fragment, page_num=idx)

    if succeeded == 0:
        raise PipelineError("No pages could be extracted. Check HF_TOKEN and model availability.")

    return merger.finalize()


# FUTURE: expose public API (Pipeline.run, Pipeline.run_from_bytes) here.
