"""Single-page extraction harness.

One PageContent -> one PageFragment via an LLM. The correct LLM (text vs
vision) is chosen per page, with one corrective retry when output isn't valid
JSON/schema. Uses the ``parse_fragment_response`` helper from ``llm``.
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage

from ocr import prompts as ocr_prompts
from ocr import llm as ocr_llm
from ocr.models import PageContent, PageFragment
from ocr.settings import Settings


class ExtractionError(Exception):
    """Raised when a page cannot be extracted after retries."""


class PageExtractor:
    """Extract one PageContent into a PageFragment using the LLM harness.

    ``set_total_pages`` must be called once before calling ``extract`` on any
    page. The extractor respects the ``retries`` budget from ``Settings`` and
    applies a single corrective retry when the LLM output can't be parsed.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._total_pages = 0

        # Pre‑build the two LLM instances (one text, one vision)
        self._text_llm = ocr_llm.create_text_llm(settings)
        self._vision_llm = ocr_llm.create_vision_llm(settings)

    def set_total_pages(self, total: int) -> None:
        self._total_pages = total

    def extract(self, page: PageContent) -> PageFragment:
        if self._total_pages == 0:
            raise ExtractionError("total_pages not set on extractor")

        # Pick appropriate LLM and message builder
        if page.kind == "text":
            messages = ocr_llm.build_text_messages(
                page.text, page.page_number, self._total_pages
            )
            llm = self._text_llm
        else:
            messages = ocr_llm.build_vision_messages(
                page.png_bytes, page.page_number, self._total_pages
            )
            llm = self._vision_llm

        return self._invoke_with_retry(llm, messages)

    def _invoke_with_retry(self, llm: Any, messages: list) -> PageFragment:
        attempt = 1
        while True:
            response = llm.invoke(messages)
            raw = response.content if isinstance(response.content, str) else str(response.content)

            try:
                # Parse JSON and validate against the PageFragment schema
                parsed_dict = ocr_llm.parse_fragment_response(raw)
                return PageFragment.model_validate(parsed_dict)
            except ValueError as parse_err:
                if attempt == 1 and self._settings.retries >= 1:
                    # One corrective retry: feed the parse error back into the model
                    messages.append(
                        HumanMessage(
                            content=(
                                "Your previous reply could not be parsed as JSON. "
                                "Respond ONLY with a valid JSON object matching this schema:\n\n"
                                f"{ocr_prompts.SYSTEM_PROMPT}\n\n"
                                f"Last raw output was:\n{raw[:300]}\n"
                                "Correct output only, nothing else."
                            )
                        )
                    )
                    attempt += 1
                    continue
                raise ExtractionError(
                    f"Failed to parse LLM output after retry. Last error: {parse_err}"
                ) from None