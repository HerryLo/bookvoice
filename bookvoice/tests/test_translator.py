import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.translator import Translator


class TestTranslator:
    """Test Translator module"""

    def setup_method(self):
        """Setup translator instance before each test"""
        self.translator = Translator()

    def test_is_english_returns_true_for_english_text(self):
        """Test that English text is correctly identified"""
        assert self.translator.is_english("Hello world") is True
        assert self.translator.is_english("This is a test") is True

    def test_is_english_returns_false_for_chinese_text(self):
        """Test that Chinese text is correctly identified"""
        assert self.translator.is_english("你好世界") is False
        assert self.translator.is_english("这是一个测试") is False

    def test_is_english_returns_false_for_mixed_text(self):
        """Test that mixed text with less than 50% English is not considered English"""
        assert self.translator.is_english("你好Hello") is False
        assert self.translator.is_english("测试test") is False

    def test_is_english_handles_empty_string(self):
        """Test empty string returns False"""
        assert self.translator.is_english("") is False

    def test_is_english_handles_special_characters(self):
        """Test special characters are handled"""
        assert self.translator.is_english("Hello! @#$%") is True

    def test_translate_to_chinese_returns_same_for_chinese(self):
        """Chinese text should pass through unchanged"""
        result = self.translator.translate_to_chinese("你好世界")
        assert result == "你好世界"

    def test_translate_to_chinese_handles_empty_string(self):
        """Empty string should return empty string"""
        result = self.translator.translate_to_chinese("")
        assert result == ""

    def test_translate_to_chinese_returns_same_for_whitespace(self):
        """Whitespace only should return unchanged"""
        result = self.translator.translate_to_chinese("   ")
        assert result == "   "
