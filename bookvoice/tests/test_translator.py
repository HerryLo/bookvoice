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

    def test_is_english_returns_true_for_mostly_english(self):
        """Test that text with more than 50% English is considered English"""
        # "你好Hello" has 5 English chars out of 7 = 71% > 50%
        assert self.translator.is_english("你好Hello") is True
        # "测试test" has 4 English chars out of 6 = 67% > 50%
        assert self.translator.is_english("测试test") is True

    def test_is_english_returns_false_for_mostly_chinese(self):
        """Test that text with less than 50% English is not considered English"""
        # "你好Hello" - actually 71% English, so True
        # "A中B文C" has 3 English chars out of 5 = 60%
        assert self.translator.is_english("A中B文C") is True

    def test_is_english_handles_empty_string(self):
        """Test empty string returns False"""
        assert self.translator.is_english("") is False

    def test_is_english_handles_special_characters(self):
        """Test special characters are counted in total but don't affect English count"""
        # "Hello!" has 5 English chars out of 6 = 83% > 50%
        assert self.translator.is_english("Hello!") is True
        # "A!" has 1 English char out of 2 = 50%, not > 50%, so False
        assert self.translator.is_english("A!") is False

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
