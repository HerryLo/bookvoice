import threading
import atexit
import os
from concurrent.futures import ThreadPoolExecutor
from config import Config
from modules.database import update_task_status, update_file_status, get_task, get_files_by_task, create_file_record, update_file_progress, update_file_segments
from .ocr import OCRProcessor
from .tts import TTSProcessor
from .pdf_handler import PDFHandler
from .word_handler import WordHandler

# 线程池最大工作线程数
MAX_WORKERS = 3

# ---------- 任务处理器 ----------

class TaskQueue:
    # 初始化处理器实例（OCR、TTS、PDF、Word）
    def __init__(self):
        self.processors = {
            'ocr': OCRProcessor(),
            'tts': TTSProcessor(rate=Config.TTS_RATE, voice=Config.TTS_VOICE),
            'pdf': PDFHandler(),
            'word': WordHandler(),
        }
        self.processing = False

    # 处理单个任务：OCR识别 → TTS生成MP3 → 合并（如需要）
    def process_task(self, task_id: str):
        # 获取任务信息，任务不存在则直接返回
        task = get_task(task_id)
        if not task:
            return

        # 更新任务状态为处理中
        update_task_status(task_id, 'processing')
        files = get_files_by_task(task_id)
        output_mode = task.get('output_mode', 'single')

        # 创建输出目录
        output_dir = os.path.join(Config.OUTPUT_FOLDER, task_id)
        os.makedirs(output_dir, exist_ok=True)

        # 收集所有文档的MP3路径（用于merged模式）
        all_mp3_paths = []

        # 遍历任务下所有文件
        for file_record in files:
            try:
                file_path = file_record['original_path']
                ext = os.path.splitext(file_path)[1].lower()

                # 根据文件类型提取文字
                if ext in ['.png', '.jpg', '.jpeg']:
                    # 图片文件 → OCR识别
                    text = self.processors['ocr'].extract_structured_text(file_path)
                elif ext == '.pdf':
                    # PDF文件 → PDF处理器提取
                    text = self.processors['pdf'].extract_text(file_path)
                elif ext == '.docx':
                    # Word文件 → Word处理器提取
                    text = self.processors['word'].extract_text(file_path)
                else:
                    raise ValueError(f"Unsupported file type: {ext}")

                # 按段落分割文本（分片处理，避免超长文本导致TTS失败）
                paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

                print("按段落分割文本：", paragraphs)

                # 更新文件总段落数
                update_file_segments(file_record['id'], len(paragraphs))

                # 进度回调函数
                def update_progress(processed_count):
                    update_file_progress(file_record['id'], processed_count)

                # 串行TTS生成（Windows环境下pyttsx3并行有COM问题，使用串行）
                mp3_paths = self.processors['tts'].text_to_speech_segments_with_progress(
                    paragraphs, output_dir, progress_callback=update_progress
                )

                # 文档内合并：将该文档的所有分片MP3合并成一个
                if mp3_paths:
                    from .mp3_merger import merge_mp3_files
                    doc_mp3 = os.path.join(output_dir, f'{file_record["id"]}.mp3')
                    merge_mp3_files(mp3_paths, doc_mp3)
                    all_mp3_paths.append(doc_mp3)
                    update_file_status(file_record['id'], 'completed', doc_mp3)

                # 确保进度为100%
                update_file_progress(file_record['id'], len(paragraphs))

            except Exception as e:
                # 记录失败状态，错误处理
                update_file_status(file_record['id'], 'failed')
                if not Config.SKIP_ON_ERROR:
                    raise
                self._log_error(task_id, file_record['original_path'], str(e))

        # merged模式：文档间合并
        if output_mode == 'merged' and len(all_mp3_paths) > 1:
            try:
                from .mp3_merger import merge_mp3_files
                merged_path = os.path.join(output_dir, 'merged.mp3')
                merge_mp3_files(all_mp3_paths, merged_path)
                # 更新第一个文件的mp3_path为合并后的路径
                if files:
                    update_file_status(files[0]['id'], 'completed', merged_path)
            except Exception as e:
                self._log_error(task_id, 'merged.mp3', str(e))

        # 检查是否有成功处理的文件，更新任务最终状态
        files = get_files_by_task(task_id)
        any_success = any(f['status'] == 'completed' for f in files)

        if any_success:
            update_task_status(task_id, 'completed')
        else:
            update_task_status(task_id, 'failed')

    # 记录错误日志到文件
    def _log_error(self, task_id: str, file_path: str, error: str):
        log_file = os.path.join(Config.LOG_FOLDER, f'error_{task_id}.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{file_path}: {error}\n")

# ---------- 线程池管理 ----------

# 懒加载单例模式初始化
_task_queue = None

# 获取任务队列单例实例
def get_task_queue():
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue

# 线程池执行器
_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# 程序退出时优雅关闭线程池
def _shutdown_executor():
    _executor.shutdown(wait=True)

atexit.register(_shutdown_executor)

# 异步提交任务到线程池
def process_task_async(task_id: str):
    task_queue = get_task_queue()
    _executor.submit(task_queue.process_task, task_id)
