import easyocr
from typing import List, Tuple, Optional

class OCRProcessor:
    def __init__(self, languages: List[str] = ['ch_sim', 'en']):
        self.languages = languages
        self.reader = None

    def _get_reader(self):
        if self.reader is None:
            self.reader = easyocr.Reader(self.languages, verbose=False)
        return self.reader

    def extract_text(self, image_path: str) -> List[Tuple[str, Tuple[int, int, int, int]]]:
        reader = self._get_reader()
        results = reader.readtext(image_path)
        return results

    def extract_structured_text(self, image_path: str) -> str:
        results = self.extract_text(image_path)
        lines = []
        for (bbox, text, confidence) in results:
            if confidence > 0.5 and text.strip():
                lines.append(text.strip())
        return '\n'.join(lines)
