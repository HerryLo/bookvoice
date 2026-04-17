import easyocr
import re
import cv2
import numpy as np
from typing import List, Tuple, Optional
import tempfile
import os


def is_valid_text(text: str) -> bool:
    # 最短长度检查
    if len(text.strip()) < 2:
        return False

    # 统计中文字符
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    if len(chinese_chars) > 0:
        return True  # 有中文就保留

    # 无中文：检查是否有足够的字母数字
    alphanumeric = re.findall(r'[a-zA-Z0-9]', text)
    if len(alphanumeric) >= 2:
        return True

    return False  # 既无中文又无足够字母数字，才是乱码


def preprocess_image(image_path: str) -> str:
    # 读取图像
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法读取图像: {image_path}")

    # 超分辨率放大（2x）
    img = cv2.resize(img, (img.shape[1] * 2, img.shape[0] * 2),
                     interpolation=cv2.INTER_CUBIC)

    # 保存到临时文件
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    temp_path = temp_file.name
    cv2.imwrite(temp_path, img)
    temp_file.close()

    return temp_path


class OCRProcessor:
    def __init__(self, languages: List[str] = ['ch_sim', 'en']):
        self.languages = languages
        self.reader = None

    def _get_reader(self):
        if self.reader is None:
            self.reader = easyocr.Reader(self.languages, verbose=False)
        return self.reader

    def extract_text(self, image_path: str) -> List[Tuple[str, Tuple[int, int, int, int]]]:
        # 图像预处理
        processed_path = preprocess_image(image_path)
        try:
            reader = self._get_reader()
            results = reader.readtext(processed_path)
            return results
        finally:
            # 清理临时文件
            if os.path.exists(processed_path):
                os.remove(processed_path)

    def extract_structured_text(self, image_path: str) -> str:
        results = self.extract_text(image_path)
        lines = []
        for (bbox, text, confidence) in results:
            if confidence > 0.1 and is_valid_text(text):
                lines.append(text.strip())
        return '\n'.join(lines)
