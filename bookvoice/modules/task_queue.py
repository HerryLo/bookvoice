import threading
import os
from config import Config
from database import update_task_status, update_file_status, get_task, get_files_by_task, create_file_record
from .ocr import OCRProcessor
from .translator import Translator
from .tts import TTSProcessor
from .pdf_handler import PDFHandler
from .word_handler import WordHandler

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

        output_dir = os.path.join(Config.OUTPUT_FOLDER, task_id)
        os.makedirs(output_dir, exist_ok=True)

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
                    main_mp3 = mp3_paths[0]
                    update_file_status(file_record['id'], 'completed', main_mp3)

            except Exception as e:
                update_file_status(file_record['id'], 'failed')
                if not Config.SKIP_ON_ERROR:
                    raise
                self._log_error(task_id, file_record['original_path'], str(e))

        update_task_status(task_id, 'completed')

    def _log_error(self, task_id: str, file_path: str, error: str):
        import logging
        log_file = os.path.join(Config.LOG_FOLDER, f'error_{task_id}.log')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{file_path}: {error}\n")

task_queue = TaskQueue()

def process_task_async(task_id: str):
    thread = threading.Thread(target=task_queue.process_task, args=(task_id,))
    thread.start()
