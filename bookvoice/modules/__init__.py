from .ocr import OCRProcessor
from .tts import TTSProcessor
from .pdf_handler import PDFHandler
from .word_handler import WordHandler
from .task_queue import process_task_async, get_task_queue

# pydub not compatible with Python 3.14+ (audioop removed)
# Import it lazily when needed
def get_mp3_merger():
    from .mp3_merger import merge_mp3_files
    return merge_mp3_files
