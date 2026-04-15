# BookVoice - 图文转语音系统

将图片、PDF、Word文档中的文字识别后转换为语音MP3文件。

## 环境要求

### Python

| 依赖包 | 最低版本 | 推荐版本 |
|--------|----------|----------|
| Python | 3.8+ | 3.10+ |
| Flask | 2.0 | 3.0+ |
| easyocr | 1.4 | 1.7+ |
| pyttsx3 | 2.90 | 最新 |
| pdfplumber | 0.5 | 最新 |
| python-docx | 0.8 | 最新 |
| deep-translator | 1.0.0 | 最新 |
| pydub | 0.25.0 | 最新 |
| Werkzeug | 2.0 | 3.0+ |

**推荐 Python 3.11 或 3.12**

### Node.js

| 依赖包 | 最低版本 | 推荐版本 |
|--------|----------|----------|
| Node.js | 16+ | 20 LTS |
| npm | 8+ | 10+ |
| Vite | 4.0 | 5.0+ |
| Vue | 3.3 | 3.4+ |
| Element Plus | 2.3.0 | 2.5+ |

**推荐 Node.js 20 LTS**

### 操作系统

- **Windows 10/11** (使用 Windows 本地 TTS 语音)
- macOS 和 Linux 需要额外配置 TTS 引擎

### ffmpeg (用于MP3合并)

如果使用"合并MP3"功能，需要安装 ffmpeg：

```bash
# Windows (使用 Chocolatey)
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt install ffmpeg
```

## 快速开始

### 1. 安装 Python 依赖

```bash
cd bookvoice
pip install -r requirements.txt
```

### 2. 安装 Node.js 依赖

```bash
cd frontend
npm install
```

### 3. 构建前端

```bash
npm run build
```

### 4. 启动应用

```bash
cd ..
python app.py
```

### 5. 访问

打开浏览器访问 http://localhost:5000

> 首次运行 OCR 功能时，easyocr 会下载模型文件（约 300MB），需要网络连接。

## 版本检查命令

```bash
# 检查Python版本
python --version

# 检查Node.js版本
node --version

# 检查npm版本
npm --version
```

## 项目结构

```
bookvoice/
├── app.py              # Flask主应用
├── config.py           # 配置文件
├── database.py         # 数据库模型
├── requirements.txt    # Python依赖
├── frontend/           # 前端源码
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api/
│       └── views/
├── static/             # 编译后的前端资源
├── storage/            # 存储目录
│   ├── uploads/        # 上传文件
│   └── outputs/        # 生成的MP3
├── modules/            # Python处理模块
│   ├── ocr.py
│   ├── translator.py
│   ├── tts.py
│   ├── pdf_handler.py
│   ├── word_handler.py
│   ├── mp3_merger.py
│   └── task_queue.py
├── logs/               # 错误日志
├── tests/              # 单元测试
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_database.py
│   └── test_translator.py
└── bookvoice.db        # SQLite数据库
```
