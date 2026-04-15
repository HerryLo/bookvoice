import os
from pydub import AudioSegment


def merge_mp3_files(mp3_paths: list, output_path: str) -> str:
    """
    Merge multiple MP3 files into a single MP3 file.

    Args:
        mp3_paths: List of paths to MP3 files to merge
        output_path: Path where the merged MP3 will be saved

    Returns:
        Path to the merged MP3 file
    """
    if not mp3_paths:
        raise ValueError("No MP3 files to merge")

    if len(mp3_paths) == 1:
        # Only one file, just copy it
        import shutil
        shutil.copy(mp3_paths[0], output_path)
        return output_path

    # Load all MP3 files
    combined = AudioSegment.empty()

    # Check for missing files before merging
    missing_files = [p for p in mp3_paths if not os.path.exists(p)]
    if missing_files:
        print(f"Warning: {len(missing_files)} MP3 files missing during merge: {missing_files}")

    for mp3_path in mp3_paths:
        if os.path.exists(mp3_path):
            audio = AudioSegment.from_mp3(mp3_path)
            combined += audio

    # Export merged audio
    combined.export(output_path, format='mp3')

    return output_path
