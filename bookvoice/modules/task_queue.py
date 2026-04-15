import threading
import atexit
import os
from concurrent.futures import ThreadPoolExecutor
from config import Config
from database import update_task_status, update_file_status, get_task, get_files_by_task, create_file_record
from .ocr import OCRProcessor
from .translator import Translator
from .tts import TTSProcessor
from .pdf_handler import PDFHandler
from .word_handler import WordHandler

MAX_WORKERS = 3

class TaskQueue:
    def __init__(self):
        self.processors = {
            'ocr': OCRProcessor(),
            'translator': Translator(),
            'tts': TTSProcessor(rate=Config.TTS_RATE, voice=Config.TTS_VOICE),
            'pdf': PDFHandler(),
            'word': WordHandler(),
        }
        self.processing = False

    def process_task(self, task_id: str):
        task = get_task(task_id)
        if not task:
            return

        update_task_status(task_id, 'processing')
        files = get_files_by_task(task_id)
        output_mode = task.get('output_mode', 'single')

        output_dir = os.path.join(Config.OUTPUT_FOLDER, task_id)
        os.makedirs(output_dir, exist_ok=True)

        all_mp3_paths = []

        for file_record in files:
            try:
                file_path = file_record['original_path']
                ext = os.path.splitext(file_path)[1].lower()

                # Extract text based on file type
                if ext in ['.png', '.jpg', '.jpeg']:
                    text = self.processors['ocr'].extract_structured_text(file_path)
                elif ext == '.pdf':
                    text = self.processors['pdf'].extract_text(file_path)
                elif ext == '.docx':
                    text = self.processors['word'].extract_text(file_path)
                else:
                    raise ValueError(f"Unsupported file type: {ext}")

                # Translate if needed
                translated_text = self.processors['translator'].translate_to_chinese(text)

                # Split into paragraphs
                paragraphs = [p.strip() for p in translated_text.split('\n\n') if p.strip()]

                # Generate MP3 for each paragraph
                mp3_paths = self.processors['tts'].text_to_speech_segments(paragraphs, output_dir)

                # Update file status
                if mp3_paths:
                    if output_mode == 'merged':
                        # Collect all MP3 paths for merging later
                        all_mp3_paths.extend(mp3_paths)
                        update_file_status(file_record['id'], 'completed', mp3_paths[0])
                    else:
                        # Single mode: use first MP3 as main
                        main_mp3 = mp3_paths[0]
                        update_file_status(file_record['id'], 'completed', main_mp3)

            except Exception as e:
                update_file_status(file_record['id'], 'failed')
                if not Config.SKIP_ON_ERROR:
                    raise
                self._log_error(task_id, file_record['original_path'], str(e))

        # Merge MP3 files if output_mode is 'merged'
        if output_mode == 'merged' and all_mp3_paths:
            try:
                from .mp3_merger import merge_mp3_files
                merged_path = os.path.join(output_dir, 'merged.mp3')
                merge_mp3_files(all_mp3_paths, merged_path)
                # Update first file record with merged path
                if files:
                    update_file_status(files[0]['id'], 'completed', merged_path)
            except Exception as e:
                self._log_error(task_id, 'merged.mp3', str(e))

        # Check if any files were successfully processed
        files = get_files_by_task(task_id)
        any_success = any(f['status'] == 'completed' for f in files)

        if any_success:
            update_task_status(task_id, 'completed')
        else:
            update_task_status(task_id, 'failed')

    def _log_error(self, task_id: str, file_path: str, error: str):
        log_file = os.path.join(Config.LOG_FOLDER, f'error_{task_id}.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{file_path}: {error}\n")

# Lazy initialization - don't create instance at module import time
_task_queue = None

def get_task_queue():
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue

_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

def _shutdown_executor():
    _executor.shutdown(wait=True)

atexit.register(_shutdown_executor)

def process_task_async(task_id: str):
    task_queue = get_task_queue()
    _executor.submit(task_queue.process_task, task_id)
