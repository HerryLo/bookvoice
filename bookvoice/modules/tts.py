import pyttsx3
import os
from concurrent.futures import ThreadPoolExecutor
from config import Config

class TTSProcessor:
    def __init__(self, rate: int = 150, voice: str = None):
        self.rate = rate
        self.voice = voice
        self.engine = None

    def _get_engine(self):
        if self.engine is None:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            if self.voice:
                self.engine.setProperty('voice', self.voice)
        return self.engine

    def _create_engine(self):
        # 为每个线程创建独立的引擎（解决Windows COM初始化问题）
        engine = pyttsx3.init()
        engine.setProperty('rate', self.rate)
        if self.voice:
            engine.setProperty('voice', self.voice)
        return engine

    def text_to_speech(self, text: str, output_path: str):
        engine = self._get_engine()
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        engine.stop()  # Clean up engine resources

    def text_to_speech_segments(self, segments: list, output_dir: str) -> list:
        mp3_paths = []
        for i, segment in enumerate(segments):
            if segment.strip():
                output_path = os.path.join(output_dir, f'segment_{i:04d}.mp3')
                self.text_to_speech(segment, output_path)
                mp3_paths.append(output_path)
        return mp3_paths

    def text_to_speech_segments_with_progress(self, segments: list, output_dir: str, progress_callback=None) -> list:
        # 串行生成MP3，支持进度回调
        mp3_paths = []
        for i, segment in enumerate(segments):
            if segment.strip():
                output_path = os.path.join(output_dir, f'segment_{i:04d}.mp3')
                self.text_to_speech(segment, output_path)
                mp3_paths.append(output_path)
            if progress_callback:
                progress_callback(i + 1)
        return mp3_paths

    def text_to_speech_parallel(self, segments: list, output_dir: str, progress_callback=None) -> list:
        # 多线程并行生成MP3
        mp3_paths = []
        max_workers = getattr(Config, 'TTS_PARALLEL_WORKERS', 3)

        def generate_single(segment, output_path):
            if segment.strip():
                # 每个线程创建独立的引擎（解决Windows COM初始化问题）
                engine = self._create_engine()
                try:
                    engine.save_to_file(segment, output_path)
                    engine.runAndWait()
                    return output_path
                finally:
                    engine.stop()
            return None

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, segment in enumerate(segments):
                output_path = os.path.join(output_dir, f'segment_{i:04d}.mp3')
                future = executor.submit(generate_single, segment, output_path)
                futures.append((future, output_path, i + 1))

            for future, path, processed_count in futures:
                result = future.result()
                if result:
                    mp3_paths.append(result)
                if progress_callback:
                    progress_callback(processed_count)

        return mp3_paths
