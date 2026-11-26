"""Output handling for the OCR pipeline.

Writes JSON to a file or prints to stdout. Supports pretty‑printing.
"""

import json
from typing import Any, Dict


def write_output(data: Dict[str, Dict[str, Any]], out_path: str | None, pretty: bool) -> None:
    """Serialize ``data`` as JSON and write to file or stdout."""
    json_str = json.dumps(data, ensure_ascii=False, indent=4 if pretty else None)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(json_str)
    else:
        print(json_str)