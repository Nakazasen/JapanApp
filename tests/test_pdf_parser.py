import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from frontend.services.pdf_vocab_parser import PDFVocabParser

class TestPDFVocabParser(unittest.TestCase):
    def setUp(self):
        self.parser = PDFVocabParser()

    def test_map_headers(self):
        # Test distinct headers
        row = ["Word", "Meaning", "Example"]
        mapping = self.parser._map_headers(row)
        self.assertEqual(mapping.get(0), "word")
        self.assertEqual(mapping.get(1), "meaning")
        self.assertEqual(mapping.get(2), "example")

    def test_map_headers_vietnamese(self):
        # Test Vietnamese headers
        row = ["Từ vựng", "Nghĩa", "Ví dụ"]
        mapping = self.parser._map_headers(row)
        self.assertEqual(mapping.get(0), "word")
        self.assertEqual(mapping.get(1), "meaning")
        self.assertEqual(mapping.get(2), "example")

    def test_guess_headers(self):
        # Test guessing strategy
        mapping = self.parser._guess_headers_by_position(2)
        self.assertEqual(mapping[0], "word")
        self.assertEqual(mapping[1], "meaning")

    def test_parse_text_line(self):
        # Test simple text line parsing
        line = "apple - quả táo"
        item = self.parser._parse_text_line(line)
        self.assertIsNotNone(item)
        self.assertEqual(item['word'], "apple")
        self.assertEqual(item['meaning'], "quả táo")

    def test_parse_text_line_tab(self):
        # Test tab separated
        line = "book\tsách"
        item = self.parser._parse_text_line(line)
        self.assertIsNotNone(item)
        self.assertEqual(item['word'], "book")
        self.assertEqual(item['meaning'], "sách")

if __name__ == '__main__':
    unittest.main()
