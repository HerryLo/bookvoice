from googletrans import Translator

class Translator:
    def __init__(self):
        self._translator = None

    def _get_translator(self):
        if self._translator is None:
            self._translator = Translator()
        return self._translator

    def is_english(self, text: str) -> bool:
        english_chars = 0
        for char in text:
            if ord('a') <= ord(char.lower()) <= ord('z'):
                english_chars += 1
        return english_chars > len(text) * 0.5

    def translate_to_chinese(self, text: str) -> str:
        if not text.strip():
            return text
        if not self.is_english(text):
            return text
        try:
            translator = self._get_translator()
            result = translator.translate(text, src='en', dest='zh-cn')
            return result.text
        except Exception as e:
            print(f"Translation error: {e}")
            return text
