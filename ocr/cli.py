"""Command‑line interface for the OCR pipeline.

Usage:
    python -m ocr <file> [-o OUT] [--pretty] [--dpi N]
                       [--text-model M] [--vision-model M]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from ocr.pipeline import process_file
from ocr.output import write_output
from ocr.settings import Settings


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="OCR PDF/DOCX forms into JSON.")
    parser.add_argument("file", type=str, help="Input PDF or DOCX file")
    parser.add_argument("-o", "--output", type=str, help="Output JSON file path (default: print to stdout)")
    parser.add_argument("--pretty", action="store_true", help="Pretty‑print JSON output")
    parser.add_argument("--dpi", type=int, help="DPI for rendering scanned pages (default 300)")
    parser.add_argument("--text-model", type=str, help="Override text LLM model id")
    parser.add_argument("--vision-model", type=str, help="Override vision LLM model id")
    parser.add_argument("--log-level", default="INFO", help="Logging level (default INFO)")

    args = parser.parse_args(argv)

    # Setup logging
    import logging
    logging.basicConfig(level=args.log_level.upper(), format="%(levelname)s: %(message)s")

    if not os.getenv("HF_TOKEN"):
        print("ERROR: HF_TOKEN environment variable is required. "
              "Create one at https://huggingface.co/settings/tokens.", file=sys.stderr)
        return 1

    overrides: dict[str, str] = {}
    if args.dpi:
        overrides["OCR_DPI"] = str(args.dpi)
    if args.text_model:
        overrides["OCR_TEXT_MODEL"] = args.text_model
    if args.vision_model:
        overrides["OCR_VISION_MODEL"] = args.vision_model

    settings = Settings.from_env(overrides)

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}", file=sys.stderr)
        return 1

    try:
        result = process_file(file_path, settings)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    write_output(result, args.output, args.pretty)
    return 0


if __name__ == "__main__":
    sys.exit(main())