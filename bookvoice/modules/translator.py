from deep_translator import GoogleTranslator

class Translator:
    def __init__(self):
        self._translator = None

    def _get_translator(self):
        if self._translator is None:
            self._translator = GoogleTranslator(source='en', target='zh-CN')
        return self._translator

    def is_english(self, text: str) -> bool:
        if not text:
            return False
        # 统计英文字母数量
        english_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        # 统计中文字符数量
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        # 如果中文字符多于英文字符，认为是中文，跳过翻译
        if chinese_chars > english_chars:
            return False
        return english_chars > len(text) * 0.5

    def translate_to_chinese(self, text: str) -> str:
        if not text.strip():
            return text
        if not self.is_english(text):
            return text
        try:
            result = self._get_translator().translate(text)
            return result if result else text
        except Exception as e:
            print(f"Translation error: {e}")
            return text
