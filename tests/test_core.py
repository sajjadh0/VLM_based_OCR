"""Offline unit tests for merger, parser and models (no network)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ocr.merger import Merger
from ocr.llm import parse_fragment_response
from ocr.models import PageFragment, PageContent


class TestMerger(unittest.TestCase):
    def test_single_page(self):
        m = Merger("invoice.pdf")
        frag = PageFragment(
            document_title="Invoice",
            fields={"Invoice Number": "INV-001", "Total": "$100"},
            items=[{"SKU": "A1", "Qty": "2"}],
        )
        m.add_page(frag, page_num=1)
        result = m.finalize()
        self.assertIn("Invoice", result)
        self.assertEqual(result["Invoice"]["fields"]["Invoice Number"], "INV-001")
        self.assertEqual(len(result["Invoice"]["items"]), 1)

    def test_duplicate_field_gets_page_suffix(self):
        m = Merger("po.pdf")
        m.add_page(PageFragment(document_title="PO", fields={"Date": "01/01"}, items=[]), page_num=1)
        m.add_page(PageFragment(document_title="", fields={"Date": "02/01"}, items=[]), page_num=2)
        result = m.finalize()
        fields = result["PO"]["fields"]
        self.assertEqual(fields["Date"], "01/01")
        self.assertEqual(fields["Date_p2"], "02/01")

    def test_title_fallback_to_filename(self):
        m = Merger("purchase_order_123.pdf")
        m.add_page(PageFragment(document_title="", fields={"X": "Y"}, items=[]), page_num=1)
        result = m.finalize()
        self.assertIn("purchase_order_123", result)

    def test_items_concatenated(self):
        m = Merger("bom.pdf")
        m.add_page(PageFragment(document_title="BOM", fields={}, items=[{"Item": "R1"}]), page_num=1)
        m.add_page(PageFragment(document_title="BOM", fields={}, items=[{"Item": "R2"}]), page_num=2)
        result = m.finalize()
        self.assertEqual(len(result["BOM"]["items"]), 2)


class TestParser(unittest.TestCase):
    def test_plain_json(self):
        raw = '{"document_title":"Invoice","fields":{"A":"B"},"items":[]}'
        d = parse_fragment_response(raw)
        self.assertEqual(d["document_title"], "Invoice")

    def test_fenced_json(self):
        raw = '```json\n{"document_title":"PO","fields":{},"items":[]}\n```'
        d = parse_fragment_response(raw)
        self.assertEqual(d["document_title"], "PO")

    def test_invalid_json_raises(self):
        with self.assertRaises(ValueError):
            parse_fragment_response("not json at all")


class TestModels(unittest.TestCase):
    def test_page_content_text_valid(self):
        p = PageContent(page_number=1, kind="text", text="hello")
        self.assertEqual(p.kind, "text")

    def test_page_content_image_valid(self):
        p = PageContent(page_number=1, kind="image", png_bytes=b"\x89PNG")
        self.assertEqual(p.kind, "image")

    def test_page_content_text_empty_raises(self):
        with self.assertRaises(ValueError):
            PageContent(page_number=1, kind="text", text="")

    def test_fragment_validation_cleans_fields(self):
        frag = PageFragment(document_title="T", fields={" A ": "  x  "})
        self.assertEqual(frag.fields, {"A": "x"})


if __name__ == "__main__":
    unittest.main()