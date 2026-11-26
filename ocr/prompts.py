"""Prompt contracts that every LLM call must honour.

System prompt encodes: strict JSON only, title-as-key framing, and handling of
forms/tables when present. Few-shot examples steer small models reliably.
"""

SYSTEM_PROMPT = """You extract structured data from business forms (Purchase Orders, Bills of Material, Invoices, etc.).

Output rules:
1. Return ONLY valid JSON. No markdown fences, no prose, no explanation.
2. document_title: short title of the form (e.g. "Purchase Order", "Bill of Materials"). Empty string if unclear.
3. fields: label -> value pairs exactly as worded on the page. Leave out unknown fields; do not invent them.
4. items: array of table row objects (header -> cell text). Empty array if no table.
5. Use double quotes everywhere. Single JSON object only.

Example output:
{"document_title":"Purchase Order","fields":{"PO Number":"4500123456","Date":"01/02/2026","Vendor":"ACME Corp"},"items":[{"Item":"001","Description":"Resistor 10k","Qty":"4"},{"Item":"002","Description":"Capacitor 100nF","Qty":"2"}]}
"""

FEW_SHOT: list[dict] = [
    {
        "role": "user",
        "content": "Here is page 1 of a scanned form.\n\nBill of Materials\nBOM Number: BOM-2026-014\nRevision: A\nDate: 01/02/2026\n",
    },
    {
        "role": "assistant",
        "content": '{"document_title":"Bill of Materials","fields":{"BOM Number":"BOM-2026-014","Revision":"A","Date":"01/02/2026"},"items":[]}',
    },
]


def page_prompt(page_number: int, text: str | None, total_pages: int) -> str:
    """Build the user-facing instruction text for a single page."""
    intro = (
        f"Extract this page ({page_number} of {total_pages}) into the JSON schema above.\n"
    )
    if text is not None:
        return intro + "PAGE TEXT:\n```text\n" + text.strip() + "\n```"
    return intro + "PAGE IMAGE: examine the scanned image below (attached as base64 image URL)."