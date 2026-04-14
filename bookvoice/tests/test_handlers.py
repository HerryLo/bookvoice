import pytest
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.pdf_handler import PDFHandler
from modules.word_handler import WordHandler


class TestPDFHandler:
    """Test PDFHandler module"""

    def setup_method(self):
        """Setup PDFHandler instance before each test"""
        self.handler = PDFHandler()

    def test_extract_text_returns_string(self):
        """Test that extract_text returns a string"""
        # Create a temporary PDF-like file for testing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name

        try:
            # This will fail on a non-PDF file, but tests the method exists
            with patch('pdfplumber.open') as mock_open:
                mock_page = MagicMock()
                mock_page.extract_text.return_value = "Sample text from PDF"
                mock_open.return_value.__enter__.return_value.pages = [mock_page]

                result = self.handler.extract_text(temp_path)

                assert isinstance(result, str)
        finally:
            os.unlink(temp_path)

    def test_extract_text_handles_empty_pdf(self):
        """Test that extract_text handles empty PDF"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name

        try:
            with patch('pdfplumber.open') as mock_open:
                mock_page = MagicMock()
                mock_page.extract_text.return_value = None
                mock_open.return_value.__enter__.return_value.pages = [mock_page]

                result = self.handler.extract_text(temp_path)

                assert result == ""
        finally:
            os.unlink(temp_path)


class TestWordHandler:
    """Test WordHandler module"""

    def setup_method(self):
        """Setup WordHandler instance before each test"""
        self.handler = WordHandler()

    def test_extract_text_returns_string(self):
        """Test that extract_text returns a string"""
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_path = f.name

        try:
            with patch('docx.Document') as mock_doc:
                mock_para1 = MagicMock()
                mock_para1.text = "First paragraph"

                mock_para2 = MagicMock()
                mock_para2.text = "Second paragraph"

                mock_para3 = MagicMock()
                mock_para3.text = ""  # Empty paragraph

                mock_doc.return_value.paragraphs = [mock_para1, mock_para2, mock_para3]

                result = self.handler.extract_text(temp_path)

                assert isinstance(result, str)
                assert "First paragraph" in result
                assert "Second paragraph" in result
                assert "" not in result.split('\n\n')  # Empty paragraphs filtered
        finally:
            os.unlink(temp_path)

    def test_extract_text_filters_empty_paragraphs(self):
        """Test that extract_text filters out empty paragraphs"""
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_path = f.name

        try:
            with patch('docx.Document') as mock_doc:
                mock_para1 = MagicMock()
                mock_para1.text = "Content"

                mock_para2 = MagicMock()
                mock_para2.text = "   "  # Whitespace only

                mock_doc.return_value.paragraphs = [mock_para1, mock_para2]

                result = self.handler.extract_text(temp_path)

                # Should only contain "Content", not whitespace
                assert result == "Content"
        finally:
            os.unlink(temp_path)
