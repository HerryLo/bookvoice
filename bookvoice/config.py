import os

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
    LOG_FOLDER = os.path.join(BASE_DIR, 'logs')
    DATABASE = os.path.join(BASE_DIR, 'bookvoice.db')

    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    SKIP_ON_ERROR = True
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'docx'}

    # TTS设置
    TTS_RATE = 150
    TTS_VOLUME = 1.0
    TTS_VOICE = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_ZH-CN_HUIHUI_11.0'