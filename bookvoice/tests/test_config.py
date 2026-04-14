import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config


class TestConfig:
    """Test Config module"""

    def test_base_dir_is_set(self):
        """Test that BASE_DIR is configured"""
        assert Config.BASE_DIR is not None
        assert os.path.isdir(Config.BASE_DIR)

    def test_upload_folder_exists(self):
        """Test that UPLOAD_FOLDER is configured"""
        assert Config.UPLOAD_FOLDER is not None

    def test_output_folder_exists(self):
        """Test that OUTPUT_FOLDER is configured"""
        assert Config.OUTPUT_FOLDER is not None

    def test_log_folder_exists(self):
        """Test that LOG_FOLDER is configured"""
        assert Config.LOG_FOLDER is not None

    def test_database_is_set(self):
        """Test that DATABASE path is configured"""
        assert Config.DATABASE is not None
        assert Config.DATABASE.endswith('.db')

    def test_max_content_length(self):
        """Test that MAX_CONTENT_LENGTH is 100MB"""
        assert Config.MAX_CONTENT_LENGTH == 100 * 1024 * 1024

    def test_skip_on_error_is_bool(self):
        """Test that SKIP_ON_ERROR is a boolean"""
        assert isinstance(Config.SKIP_ON_ERROR, bool)

    def test_allowed_extensions(self):
        """Test that ALLOWED_EXTENSIONS contains expected formats"""
        expected = {'png', 'jpg', 'jpeg', 'pdf', 'docx'}
        assert Config.ALLOWED_EXTENSIONS == expected

    def test_tts_rate_is_set(self):
        """Test that TTS_RATE is configured"""
        assert Config.TTS_RATE is not None
        assert Config.TTS_RATE > 0

    def test_tts_volume_is_set(self):
        """Test that TTS_VOLUME is configured"""
        assert Config.TTS_VOLUME is not None
        assert 0 <= Config.TTS_VOLUME <= 1.0
