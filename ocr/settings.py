"""Configuration for the OCR pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass

HF_ROUTER_BASE_URL = "https://router.huggingface.co/v1"
DEFAULT_TEXT_MODEL = "Qwen/Qwen2.5-3B-Instruct"
DEFAULT_VISION_MODEL = "Qwen/Qwen2-VL-2B-Instruct"
DEFAULT_MAX_TOKENS = 1024
DEFAULT_DPI = 300
DEFAULT_RETRIES = 2


@dataclass(frozen=True)
class Settings:
    hf_token: str
    text_model: str
    vision_model: str
    hf_router_base_url: str = HF_ROUTER_BASE_URL
    max_tokens: int = DEFAULT_MAX_TOKENS
    dpi: int = DEFAULT_DPI
    retries: int = DEFAULT_RETRIES

    @classmethod
    def from_env(cls, overrides: dict[str, str] | None = None) -> "Settings":
        merged = dict(os.environ)
        if overrides:
            merged.update(overrides)
        return cls(
            hf_token=merged.get("HF_TOKEN", ""),
            text_model=merged.get("OCR_TEXT_MODEL", DEFAULT_TEXT_MODEL),
            vision_model=merged.get("OCR_VISION_MODEL", DEFAULT_VISION_MODEL),
            hf_router_base_url=merged.get("OCR_HF_ROUTER_BASE_URL", HF_ROUTER_BASE_URL),
            max_tokens=int(merged.get("OCR_MAX_TOKENS", DEFAULT_MAX_TOKENS)),
            dpi=int(merged.get("OCR_DPI", DEFAULT_DPI)),
            retries=int(merged.get("OCR_RETRIES", DEFAULT_RETRIES)),
        )
