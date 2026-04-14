from docx import Document

class WordHandler:
    def extract_text(self, docx_path: str) -> str:
        doc = Document(docx_path)
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text)
        return '\n\n'.join(paragraphs)
