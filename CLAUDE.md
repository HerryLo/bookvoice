# BookVoice 项目

## 项目位置

项目根目录：`D:\dev\Claude Code Test\bookvoice`
配置文件：`D:\dev\Claude Code Test\CLAUDE.md`
项目文档：`D:\dev\Claude Code Test\README.md`

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
│   ├── translator.py         # 翻译（deep-translator）
│   ├── tts.py               # TTS处理
│   ├── pdf_handler.py       # PDF处理
│   ├── word_handler.py      # Word处理
│   └── mp3_merger.py        # MP3合并
├── storage/                  # 存储目录
│   ├── uploads/             # 上传文件
│   └── outputs/             # 生成的MP3
├── logs/                     # 错误日志
├── tests/                    # 单元测试
│   ├── test_config.py
│   ├── test_database.py
│   └── test_translator.py
├── install.bat               # Windows 一键安装脚本
├── install.sh                # macOS/Linux 一键安装脚本
└── bookvoice.db            # SQLite数据库
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
|-----|------|------|
| GET | /api/tasks | 获取任务列表 |
| GET | /api/task/<id> | 获取任务详情（含文件列表） |
| GET | /api/task/<id>/progress | 获取任务处理进度（含百分比） |
| POST | /api/upload | 上传文件（支持 output_mode: single/merged） |
| GET | /api/task/<id>/download | 下载MP3（single=ZIP, merged=单一MP3） |
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
- `total_segments` INTEGER（总分片数，用于进度计算）
- `processed_segments` INTEGER（已处理分片数，用于进度计算）

### 索引
- `idx_files_task_id` ON files(task_id)`
- `idx_tasks_status` ON tasks(status)

---

## 输出模式说明

### Single 模式（默认）
1. 每个文档按 `\n\n` 分割成段落，分片 TTS 生成 MP3
2. 同一文档内的分片 MP3 合并成该文档的单一 MP3
3. 下载时：单文档返回单个 MP3，多文档打包 ZIP

### Merged 模式
1. 每个文档按 Single 模式各自处理（分片 → TTS → 文档内合并）
2. 收集所有文档的 MP3 路径
3. 所有 MP3 合并成一个大 MP3（`merged.mp3`）
4. 下载时：直接返回这一个合并后的 MP3

### 进度计算
```
进度 = Σ(每个文件的 processed_segments) / Σ(每个文件的 total_segments) × 100%
```
- TTS 每完成一个分片更新一次进度
- 文档内合并完成后进度为 100%
- Merged 模式文档间合并完成后进度为 100%

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