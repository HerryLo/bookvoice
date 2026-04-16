import os
import subprocess
import tempfile
import shutil


def merge_mp3_files(mp3_paths: list, output_path: str) -> str:
    """
    Merge multiple MP3 files into a single MP3 file using ffmpeg.
    Properly handles MP3 concatenation without ID3 tag issues.

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

    # Use ffmpeg with filter_complex for reliable concatenation
    # Create input arguments for all files
    input_args = []
    for f in existing_files:
        input_args.extend(['-i', f])

    # Use ffmpeg to concat all MP3 files
    result = subprocess.run([
        'ffmpeg', '-y',
        *input_args,
        '-filter_complex', f'concat=n={len(existing_files)}:v=0:a=1',
        '-c:a', 'libmp3lame',
        output_path
    ], capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg merge failed: {result.stderr}")

    return output_path
