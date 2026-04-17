import os
import subprocess
import tempfile
import shutil


def merge_mp3_files(mp3_paths: list, output_path: str) -> str:
    """
    Merge multiple MP3 files into a single MP3 file using ffmpeg concat demuxer.
    Ensures browser-compatible MP3 output.

    Args:
        mp3_paths: List of paths to MP3 files to merge
        output_path: Path where the merged MP3 will be saved

    Returns:
        Path to the merged MP3 file
    """
    if not mp3_paths:
        raise ValueError("No MP3 files to merge")

    # Filter to only existing files
    existing_files = [p for p in mp3_paths if os.path.exists(p)]
    if not existing_files:
        raise ValueError("No MP3 files found to merge")

    if len(existing_files) == 1:
        # Only one file, just copy it
        shutil.copy(existing_files[0], output_path)
        return output_path

    # Method: Use concat demuxer - most reliable for browser compatibility
    # Create temporary file list for concat demuxer
    list_file = None
    try:
        list_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        )
        for mp3 in existing_files:
            list_file.write(f"file '{mp3}'\n")
        list_file.close()

        # Use ffmpeg concat demuxer with -c copy for fast merge
        result = subprocess.run([
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', list_file.name,
            '-c', 'copy',
            '-b:a', '192k',
            '-ar', '44100',
            '-ac', '2',
            output_path
        ], capture_output=True, text=True)

        if result.returncode != 0:
            # Fallback: re-encode if concat copy fails
            result = subprocess.run([
                'ffmpeg', '-y',
                '-f', 'concat', '-safe', '0',
                '-i', list_file.name,
                '-c:a', 'libmp3lame',
                '-b:a', '192k',
                '-ar', '44100',
                '-ac', '2',
                output_path
            ], capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg merge failed: {result.stderr}")

    finally:
        # Cleanup temp file
        if list_file and os.path.exists(list_file.name):
            os.remove(list_file.name)

    return output_path
