import pytest
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.mp3_merger import merge_mp3_files


class TestMP3Merger:
    """Test MP3 merger module"""

    def test_merge_mp3_files_raises_error_for_empty_list(self):
        """Test that merge_mp3_files raises ValueError for empty list"""
        with pytest.raises(ValueError):
            merge_mp3_files([], 'output.mp3')

    def test_merge_mp3_files_with_single_file(self):
        """Test that merge_mp3_files copies single file directly"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            input_path = f.name

        output_path = tempfile.mktemp(suffix='.mp3')

        try:
            with patch('shutil.copy') as mock_copy:
                result = merge_mp3_files([input_path], output_path)

                assert result == output_path
                mock_copy.assert_called_once()
        finally:
            os.unlink(input_path)
            try:
                os.unlink(output_path)
            except:
                pass

    def test_merge_mp3_files_with_multiple_files(self):
        """Test merging multiple MP3 files"""
        files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                files.append(f.name)

        output_path = tempfile.mktemp(suffix='.mp3')

        try:
            with patch('pydub.AudioSegment') as mock_audio:
                mock_instance = MagicMock()
                mock_audio.from_mp3.return_value = mock_instance
                mock_instance.__iadd__ = MagicMock(return_value=mock_instance)
                mock_instance.export = MagicMock()

                result = merge_mp3_files(files, output_path)

                assert result == output_path
                assert mock_audio.from_mp3.call_count == 3
                mock_instance.export.assert_called_once()
        finally:
            for f in files:
                os.unlink(f)
            try:
                os.unlink(output_path)
            except:
                pass
