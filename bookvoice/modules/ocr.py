import easyocr
from typing import List, Tuple

class OCRProcessor:
    def __init__(self, languages: List[str] = ['ch_sim', 'en']):
        self.reader = easyocr.Reader(languages, verbose=False)

    def extract_text(self, image_path: str) -> List[Tuple[str, Tuple[int, int, int, int]]]:
        results = self.reader.readtext(image_path)
        return results

    def extract_structured_text(self, image_path: str) -> str:
        results = self.extract_text(image_path)
        lines = []
        for (bbox, text, confidence) in results:
            if confidence > 0.3 and text.strip():
                lines.append(text.strip())
        return '\n'.join(lines)
