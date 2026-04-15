# BookVoice - 图文转语音系统

将图片、PDF、Word文档中的文字识别后转换为语音MP3文件。

## 功能特性

- **OCR文字识别** - 支持 PNG、JPG 图片识别
- **文档解析** - 支持 PDF、DOCX 文档
- **翻译** - 英文内容自动翻译为中文
- **语音合成** - 文字转MP3语音
- **批量处理** - 支持批量上传和合并MP3输出
- **任务管理** - 完整的任务状态跟踪（待处理/处理中/已完成/失败）
- **删除功能** - 支持删除任务和单个文件

## 环境要求

### Python

| 依赖包 | 最低版本 | 推荐版本 |
|--------|----------|----------|
| Python | 3.8+ | 3.11+ |
| Flask | 2.0 | 3.0+ |
| deep-translator | 1.0.0 | 最新 |
| easyocr | 1.4 | 1.7+ |
| pyttsx3 | 2.90 | 最新 |
| pdfplumber | 0.5 | 最新 |
| python-docx | 0.8 | 最新 |
| pydub | 0.25.0 | 最新 |
| Werkzeug | 2.0 | 3.0+ |

### Node.js

| 依赖包 | 最低版本 | 推荐版本 |
|--------|----------|----------|
| Node.js | 16+ | 20 LTS |
| npm | 8+ | 10+ |
| Vite | 4.0 | 5.0+ |
| Vue | 3.3 | 3.4+ |
| Element Plus | 2.3.0 | 2.5+ |

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

## API 认证

所有 API 请求需要在 Header 中添加 `X-API-Key`：

```bash
curl -H "X-API-Key: dev-key-change-me" http://127.0.0.1:5000/api/tasks
```

可通过环境变量 `BOOKVOICE_API_KEY` 修改默认密钥。

## API 端点

| 方法 | 路径 | 说明 |
|-----|------|-----|
| GET | /api/tasks | 获取任务列表 |
| GET | /api/task/<id> | 获取任务详情（含文件列表） |
| POST | /api/upload | 上传文件 |
| GET | /api/task/<id>/download | 下载MP3 |
| POST | /api/task/<id>/retry | 重试失败任务 |
| DELETE | /api/task/<id> | 删除任务 |
| DELETE | /api/file/<id> | 删除单个文件 |
| GET | /api/logs | 获取日志列表 |
| GET | /api/logs/<filename> | 获取日志内容 |

## 项目结构

```
bookvoice/
├── app.py              # Flask主应用
├── config.py           # 配置文件
├── requirements.txt    # Python依赖
├── frontend/           # 前端源码
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api/
│       │   └── index.js
│       └── views/
│           ├── TaskList.vue
│           ├── Upload.vue
│           └── Logs.vue
├── static/             # 编译后的前端资源
├── storage/           # 存储目录
│   ├── uploads/       # 上传文件
│   └── outputs/       # 生成的MP3
├── modules/            # Python处理模块
│   ├── database.py     # 数据库操作
│   ├── task_queue.py   # 任务队列
│   ├── ocr.py         # OCR处理
│   ├── translator.py   # 翻译
│   ├── tts.py         # TTS处理
│   ├── pdf_handler.py # PDF处理
│   ├── word_handler.py# Word处理
│   └── mp3_merger.py  # MP3合并
├── logs/              # 错误日志
├── tests/             # 单元测试
└── bookvoice.db       # SQLite数据库
```

## 数据库

### 表结构

**tasks 表**
- `id` TEXT PRIMARY KEY
- `filename` TEXT
- `status` TEXT（pending/processing/completed/failed）
- `output_mode` TEXT（single/merged）
- `created_at` DATETIME
- `completed_at` DATETIME

**files 表**
- `id` INTEGER PRIMARY KEY
- `task_id` TEXT
- `original_path` TEXT
- `mp3_path` TEXT
- `status` TEXT

### 索引
- `idx_files_task_id` ON files(task_id)
- `idx_tasks_status` ON tasks(status)

## 测试

```bash
cd bookvoice
pytest tests/ -v
```

## 版本检查

```bash
# 检查Python版本
python --version

# 检查Node.js版本
node --version

# 检查npm版本
npm --version
```
