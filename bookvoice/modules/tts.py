import pyttsx3
import os

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

    def text_to_speech(self, text: str, output_path: str):
        engine = self._get_engine()
        engine.save_to_file(text, output_path)
        engine.runAndWait()

    def text_to_speech_segments(self, segments: list, output_dir: str) -> list:
        mp3_paths = []
        for i, segment in enumerate(segments):
            if segment.strip():
                output_path = os.path.join(output_dir, f'segment_{i:04d}.mp3')
                self.text_to_speech(segment, output_path)
                mp3_paths.append(output_path)
        return mp3_paths
