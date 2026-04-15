# BookVoice 项目

## 项目位置

项目根目录：`D:\dev\Claude Code Test\bookvoice`
配置文件：`D:\dev\Claude Code Test\CLAUDE.md`
项目文档：`D:\dev\Claude Code Test\README.md`

## 项目概述

将图片、PDF、Word文档中的文字识别后转换为语音MP3文件。

### 功能特性
- OCR文字识别（easyocr）
- 英文→中文翻译（deep-translator）
- 文字转语音（pyttsx3 Windows TTS）
- MP3合并功能
- 批量处理
- 任务管理（自动刷新）
- 删除功能（任务/文件）

---

## 项目结构

```
bookvoice/
├── app.py                    # Flask主应用（API端口）
├── config.py                 # 配置文件
├── requirements.txt          # Python依赖
├── frontend/                # 前端源码（Vue3 + Element Plus）
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api/index.js     # API调用（含X-API-Key）
│       └── views/
│           ├── TaskList.vue  # 任务列表（自动刷新）
│           ├── Upload.vue     # 文件上传
│           └── Logs.vue       # 日志查看
├── static/                   # 编译后的前端资源
├── modules/                  # Python处理模块
│   ├── database.py          # 数据库操作
│   ├── task_queue.py        # 任务队列（ThreadPoolExecutor）
│   ├── ocr.py               # OCR处理
│   ├── translator.py        # 翻译（deep-translator）
│   ├── tts.py              # TTS处理
│   ├── pdf_handler.py      # PDF处理
│   ├── word_handler.py     # Word处理
│   └── mp3_merger.py       # MP3合并
├── storage/                 # 存储目录
│   ├── uploads/            # 上传文件
│   └── outputs/            # 生成的MP3
├── logs/                    # 错误日志
├── tests/                   # 单元测试
│   ├── test_config.py
│   ├── test_database.py
│   └── test_translator.py
└── bookvoice.db           # SQLite数据库
```

---

## 代码注释规范

### Python 代码注释
- 使用 `#` 作为注释开头，**禁止使用 `"""` docstring 形式**
- 每个函数/方法需要添加注释说明功能
- API 路由注释格式：`# HTTP方法 /api/路径 - 功能描述`

```python
# GET /api/tasks - 获取所有任务列表
def get_tasks():
    tasks = get_all_tasks()
    return jsonify(tasks), 200

# POST /api/upload - 上传文件创建新任务
def upload():
    files = request.files.getlist('files')
    ...
```

### API 路由分组
按功能将 API 路由分组，每组用分隔注释标记：
- `# ---------- 任务相关 ----------`
- `# ---------- 文件相关 ----------`
- `# ---------- 上传相关 ----------`
- `# ---------- 日志相关 ----------`

---

## 技术栈

### Python 依赖
- Flask >= 2.0
- deep-translator >= 1.0.0（翻译）
- easyocr >= 1.4（OCR）
- pyttsx3 >= 2.90（TTS）
- pdfplumber >= 0.5
- python-docx >= 0.8
- pydub >= 0.25.0（MP3合并）

### Node.js 依赖
- Vue >= 3.3
- Element Plus >= 2.3
- axios >= 1.4
- vite >= 4.0

---

## API 认证

所有 API 请求需要 `X-API-Key` header：

```bash
curl -H "X-API-Key: dev-key-change-me" http://127.0.0.1:5000/api/tasks
```

可通过环境变量 `BOOKVOICE_API_KEY` 修改密钥。

### 主要 API 端点

| 方法 | 路径 | 说明 |
|-----|------|-----|
| GET | /api/tasks | 获取任务列表 |
| GET | /api/task/<id> | 获取任务详情（含文件列表） |
| POST | /api/upload | 上传文件 |
| GET | /api/task/<id>/download | 下载MP3 |
| POST | /api/task/<id>/retry | 重试失败任务 |
| DELETE | /api/task/<id> | 删除任务（只能删除completed/failed） |
| DELETE | /api/file/<id> | 删除单个文件 |
| GET | /api/logs | 获取日志列表 |
| GET | /api/logs/<filename> | 获取日志内容 |

---

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
- `task_id` TEXT（外键）
- `original_path` TEXT
- `mp3_path` TEXT
- `status` TEXT

### 索引
- `idx_files_task_id` ON files(task_id)
- `idx_tasks_status` ON tasks(status)

---

## 配置项（config.py）

| 配置项 | 默认值 | 说明 |
|-------|-------|------|
| BASE_DIR | 项目根目录 | 基础路径 |
| STORAGE_FOLDER | storage | 存储根目录 |
| UPLOAD_FOLDER | storage/uploads | 上传目录 |
| OUTPUT_FOLDER | storage/outputs | 输出目录 |
| LOG_FOLDER | logs | 日志目录 |
| DATABASE | bookvoice.db | 数据库路径 |
| MAX_CONTENT_LENGTH | 100MB | 最大文件大小 |
| SKIP_ON_ERROR | True | 错误时跳过继续 |
| TTS_RATE | 150 | 语音速率 |
| TTS_VOICE | Windows注册表路径 | 语音引擎 |

---

## 启动应用

```bash
cd D:\dev\Claude Code Test\bookvoice
py app.py
```

访问 http://localhost:5000

---

## 前端构建

```bash
cd D:\dev\Claude Code Test\bookvoice\frontend
npm install
npm run build   # 输出到 ../static/
```

---

## 测试

```bash
cd D:\dev\Claude Code Test\bookvoice
py -m pytest tests/ -v
```

---

## 首次运行

- **OCR模型下载**：easyocr 首次运行会下载模型文件（约300MB）
- **ffmpeg**：MP3合并功能需要安装 ffmpeg

```bash
# Windows
choco install ffmpeg

# macOS
brew install ffmpeg
```

---

## 常见问题

### Python 版本
- 推荐 Python 3.11 或 3.12
- Python 3.14 兼容（pydub 延迟导入已处理）

### TTS 语音
- 仅支持 Windows（使用系统语音）
- 语音路径：`HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_ZH-CN_HUIHUI_11.0`

### 任务一直显示"处理中"
- 任务在后台异步处理
- 任务列表会自动刷新（每3秒）
- 处理完成后状态会更新为"已完成"或"失败"

### API 返回 401 Unauthorized
- 前端已配置默认 API Key：`dev-key-change-me`
- 可通过环境变量 `BOOKVOICE_API_KEY` 修改
