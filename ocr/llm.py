"""Hugging Face router client builders for LangChain with structured output.

Wraps ChatOpenAI against ``https://router.huggingface.co/v1`` with a single HF
token. Provides text‑only and vision‑capable LLM instances plus message builders
for single pages.
"""

from __future__ import annotations

import base64
from typing import Any, List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ocr import prompts as ocr_prompts
from ocr.settings import Settings


def create_text_llm(settings: Settings) -> ChatOpenAI:
    """Text‑oriented LLM via HuggingFace router."""
    return ChatOpenAI(
        model=settings.text_model,
        base_url=settings.hf_router_base_url,
        api_key=settings.hf_token,
        temperature=0,
        max_tokens=settings.max_tokens,
    )


def create_vision_llm(settings: Settings) -> ChatOpenAI:
    """Vision‑capable LLM for scanned page images via HuggingFace router."""
    return ChatOpenAI(
        model=settings.vision_model,
        base_url=settings.hf_router_base_url,
        api_key=settings.hf_token,
        temperature=0,
        max_tokens=settings.max_tokens,
    )


def _vision_content_block(png_bytes: bytes, page_number: int) -> List[Any]:
    b64 = base64.b64encode(png_bytes).decode("utf-8")
    return [
        {"type": "text", "text": f"PAGE IMAGE (page {page_number}):"},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
    ]


def build_text_messages(text: str, page_number: int, total_pages: int) -> List[Any]:
    """LangChain message list for an embedded‑text page."""
    user_text = ocr_prompts.page_prompt(page_number, text, total_pages)
    messages: List[Any] = [SystemMessage(content=ocr_prompts.SYSTEM_PROMPT)]
    # Few‑shot pair guides small models reliably toward the exact JSON contract
    messages.append(HumanMessage(content=ocr_prompts.FEW_SHOT[0]["content"]))
    messages.append(AIMessage(content=ocr_prompts.FEW_SHOT[1]["content"]))
    messages.append(HumanMessage(content=user_text))
    return messages


def build_vision_messages(png_bytes: bytes, page_number: int, total_pages: int) -> List[Any]:
    """LangChain message list for a scanned‑image page."""
    messages: List[Any] = [SystemMessage(content=ocr_prompts.SYSTEM_PROMPT)]
    messages.append(HumanMessage(content=ocr_prompts.FEW_SHOT[0]["content"]))
    messages.append(AIMessage(content=ocr_prompts.FEW_SHOT[1]["content"]))
    content_block = _vision_content_block(png_bytes, page_number)
    content_block.append(
        {
            "type": "text",
            "text": ocr_prompts.page_prompt(page_number, None, total_pages),
        }
    )
    messages.append(HumanMessage(content=content_block))
    return messages


def parse_fragment_response(raw: str) -> Any:
    """Robust JSON parsing of an LLM reply into a dict (validated later)."""
    stripped = raw.strip()

    # Strip markdown code fences if present
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        inside = False
        code_lines = []
        for line in lines:
            if line.strip().startswith("```"):
                inside = not inside
                continue
            if inside:
                code_lines.append(line)
        stripped = "\n".join(code_lines)

    import json

    return json.loads(stripped)