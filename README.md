# OCR‑to‑JSON for Business Forms (PDF/DOCX)

A local CLI tool that reads **PDF** or **DOCX** forms and produces a single JSON
file with the document structure as `{ "Title": { "fields": {…}, "items": [...] } }`.

Powered by **Hugging Face Inference Providers** (routed through OpenRouter) and
LangChain with small 3B‑parameter models for fast, reliable extraction.

---

## Quick start

1. **Install Python 3.10+**
   ```powershell
   python --version
   ```

2. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Create an HF token**
   - Visit <https://huggingface.co/settings/tokens>
   - Create a token with **Inference** permission
   - Copy the token

4. **Set up environment**
   ```powershell
   copy .env.example .env
   # Edit .env and set HF_TOKEN=...
   ```

5. **Run**
   ```powershell
   python -m ocr path/to/invoice.pdf -o invoice.json --pretty
   ```

   (No `--pretty`? Just print to stdout.)

---

## What it does

For every page in the file:
- **If the PDF has a text layer** → extract the text and send it to a small
  text‑focused LLM (e.g., `Qwen/Qwen2.5-3B-Instruct` by default) via the HF router.
- **If the page is scanned (no text layer)** → render the page at 300 DPI,
  base64‑encode the PNG, and send to a small vision LLM (default
  `Qwen/Qwen2-VL-2B-Instruct`).

The LLM returns a JSON fragment per page:
```json
{
  "document_title": "Purchase Order",
  "fields": {"PO Number": "4500123456", "Date": "01/02/2026"},
  "items": []
}
```

After all pages are processed, the fragments are merged:
- One top‑level JSON object.
- `document_title`: first non‑empty title wins (fallback: file name without
  extension).
- `fields`: merged; duplicate keys across pages get suffix `_<page_number>`
  (e.g. `Invoice_Date_p3`).
- `items`: concatenated array across pages.

Final output:
```json
{
  "Purchase Order": {
    "fields": {
      "PO Number": "4500123456",
      "Date": "01/02/2026"
    },
    "items": [
      {"Item": "001", "Description": "Resistor 10k", "Qty": "4"}
    ]
  }
}
```

---

## CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output` | `None` | Write JSON to file. If omitted, prints to stdout. |
| `--pretty` | `False` | Pretty‑print JSON (4‑space indent). |
| `--dpi` | `300` | Render resolution for scanned pages. Higher → better OCR but slower. |
| `--text-model` | `Qwen/Qwen2.5-3B-Instruct` | Override text LLM model id. |
| `--vision-model` | `Qwen/Qwen2-VL-2B-Instruct` | Override vision LLM model id. |
| `--log-level` | `INFO` | Set logging level (`DEBUG`, `INFO`, `WARNING`, …). |
| `-h, --help` | – | Show help message. |

Environment variables (via `.env` or exported):

| Variable | Description |
|----------|-------------|
| `HF_TOKEN` | **Required.** Your Hugging Face token with Inference permission. |
| `OCR_TEXT_MODEL` | Override default text LLM. |
| `OCR_VISION_MODEL` | Override default vision LLM. |
| `OCR_HF_ROUTER_BASE_URL` | HF router base URL (default `https://router.huggingface.co/v1`). |
| `OCR_MAX_TOKENS` | Max output tokens per LLM call (default `1024`). |
| `OCR_DPI` | Default DPI for rendering (default `300`). |
| `OCR_RETRIES` | Number of corrective retries on parse failure (default `2`). |

---

## Dependencies

- **PyMuPDF** — extracts embedded text and renders PDF pages to PNG.
- **python-docx** — reads `.docx` files (paragraphs + tables).
- **langchain** & **langchain-openai** — prompt orchestration and structured
  output wrappers.
- **Pillow** — optional image utilities (included for future use).
- **python-dotenv** — loads `.env` variables.

---

## SOLID Design Overview

- **Single Responsibility** – each module has one job:
  - `loaders` – file → page list.
  - `extractor` – page → fragment.
  - `merger` – fragments → final JSON.
  - `cli` – argument parsing & wiring.
- **Open/Closed** – new file types are added by creating a new `DocumentLoader`
  implementation and registering it; existing code untouched.
- **Liskov Substitution** – all loaders implement `DocumentLoader` protocol.
- **Interface Segregation** – narrow protocols for each role (`DocumentLoader`,
  `PageExtractor`, `Merger`).
- **Dependency Inversion** – `cli.py` depends on abstractions
  (`LoaderRegistry`, `PageExtractor`, `Merger`, `Settings`) and concrete
  implementations are injected at runtime.

---

## Examples

### 1. Simple PO PDF
```powershell
python -m ocr "sample_po.pdf" --pretty
```

### 2. Multiple pages with duplicate fields
```powershell
python -m ocr "bill_of_materials.pdf" -o bom.json
```
If page 2 has the same field as page 1, you'll see `field_p2` in JSON.

### 3. Vision‑only scan
```powershell
python -m ocr "scan_image.pdf" --dpi 400
```

### 4. Custom model
```powershell
python -m ocr "form.docx" --text-model "Qwen/Qwen2.5-1.5B-Instruct"
```

---

## Limitations & Caveats

- **Free HF inference tier** is limited. For production workloads, consider
  upgrading to PRO ($2/month) or using paid credits.
- **Scanned pages** use a vision LLM. Image quality matters—use high DPI for
  messy scans.
- **DOCX** – only `.docx` supported; `.doc` must be converted first.
- **No OCR fallback** – if the LLM fails to parse a page, that page is skipped
  with a warning (the tool tries a corrective retry first).

---

## License

MIT