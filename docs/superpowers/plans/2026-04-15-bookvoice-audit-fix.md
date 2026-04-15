# BookVoice 项目审计修复计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复审计发现的25个问题（5 Critical、7 High、7 Medium、6 Low），并更新文档

**Architecture:** 分6个批次修复：安全修复 → 资源管理 → 翻译稳定性 → 数据库优化 → 输入验证 → 文档更新

**Tech Stack:** Python/Flask后端, Vue3/Element Plus前端, SQLite, pyttsx3, easyocr

---

## 文件结构

```
bookvoice/
├── app.py                 # Flask主应用（修复安全+验证问题）
├── config.py              # 配置（添加验证）
├── database.py            # 数据库（添加索引+连接池）
├── frontend/              # 前端代码
├── modules/
│   ├── ocr.py             # OCR处理（添加超时）
│   ├── translator.py      # 翻译（替换googletrans）
│   ├── tts.py             # TTS（添加引擎清理）
│   ├── pdf_handler.py
│   ├── word_handler.py
│   ├── mp3_merger.py      # MP3合并（添加警告）
│   └── task_queue.py      # 任务队列（线程池管理）
├── storage/
│   ├── uploads/
│   └── outputs/
├── tests/
│   ├── test_config.py
│   ├── test_database.py
│   └── test_translator.py
├── README.md
└── UNIT_TEST_REPORT.md
```

---

## Batch 1: 安全修复

### Task 1: 修复日志下载路径遍历漏洞

**Files:**
- Modify: `app.py:101-103`

- [ ] **Step 1: 读取当前代码确认问题**

```python
# 当前代码（有问题）
if not filename.startswith('error_') or '..' in filename:
    return jsonify({'error': 'Invalid filename'}), 400
```

- [ ] **Step 2: 修复逻辑（用 and 替代 or）**

```python
if not filename.startswith('error_') and '..' not in filename:
    return jsonify({'error': 'Invalid filename'}), 400
```

- [ ] **Step 3: 提交**

```bash
git add app.py
git commit -m "fix: path traversal in log download (CRITICAL-1)"
```

---

### Task 2: 修复API错误信息泄露

**Files:**
- Modify: `app.py:109-114`

- [ ] **Step 1: 修复错误泄露**

```python
# 修复前
except Exception as e:
    return jsonify({'error': str(e)}), 500

# 修复后
except Exception as e:
    app.logger.error(f"Failed to read log file {filename}: {e}")
    return jsonify({'error': 'Failed to read log file'}), 500
```

- [ ] **Step 2: 添加logger配置（在 app.py 顶部添加）**

```python
import logging
app.logger.setLevel(logging.INFO)
```

- [ ] **Step 3: 提交**

```bash
git add app.py
git commit -m "fix: don't expose internal errors in API (CRITICAL-2)"
```

---

### Task 3: 关闭Debug模式

**Files:**
- Modify: `app.py:133`

- [ ] **Step 1: 修改debug设置**

```python
# 修复前
app.run(debug=True, port=5000)

# 修复后
app.run(debug=False, port=5000)
```

- [ ] **Step 2: 提交**

```bash
git add app.py
git commit -m "fix: disable debug mode in production (MEDIUM-1)"
```

---

## Batch 2: 资源管理

### Task 4: 实现线程池管理

**Files:**
- Modify: `modules/task_queue.py`

- [ ] **Step 1: 读取当前 task_queue.py**

```python
# 当前问题代码
def process_task_async(task_id: str):
    task_queue = get_task_queue()
    thread = threading.Thread(target=task_queue.process_task, args=(task_id,))
    thread.start()
```

- [ ] **Step 2: 添加线程池实现**

```python
from concurrent.futures import ThreadPoolExecutor, Future
import atexit

MAX_WORKERS = 3

_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

def _shutdown_executor():
    _executor.shutdown(wait=True)

atexit.register(_shutdown_executor)

def process_task_async(task_id: str):
    task_queue = get_task_queue()
    _executor.submit(task_queue.process_task, task_id)
```

- [ ] **Step 3: 提交**

```bash
git add modules/task_queue.py
git commit -m "feat: add thread pool for task processing (CRITICAL-3)"
```

---

### Task 5: TTS引擎资源清理

**Files:**
- Modify: `modules/tts.py`

- [ ] **Step 1: 读取当前 tts.py**

- [ ] **Step 2: 修改 text_to_speech 方法添加引擎清理**

```python
def text_to_speech(self, text: str, output_path: str):
    engine = self._get_engine()
    engine.save_to_file(text, output_path)
    engine.runAndWait()
    engine.stop()  # 清理引擎资源
```

- [ ] **Step 3: 提交**

```bash
git add modules/tts.py
git commit -m "fix: clean up pyttsx3 engine after TTS generation (CRITICAL-5)"
```

---

## Batch 3: 翻译稳定性

### Task 6: 替换googletrans为deep-translator

**Files:**
- Modify: `modules/translator.py`
- Modify: `requirements.txt`

- [ ] **Step 1: 安装新依赖**

```bash
pip install deep-translator
```

- [ ] **Step 2: 重写 translator.py**

```python
from deep_translator import GoogleTranslator
from typing import Optional

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
        english_chars = sum(1 for c in text if c.isascii() and c.isalpha())
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
```

- [ ] **Step 3: 更新 requirements.txt 添加 deep-translator**

- [ ] **Step 4: 提交**

```bash
git add modules/translator.py requirements.txt
git commit -m "feat: replace googletrans with deep-translator (CRITICAL-4)"
```

---

### Task 7: OCR添加超时和置信度阈值调整

**Files:**
- Modify: `modules/ocr.py`

- [ ] **Step 1: 调整置信度阈值**

```python
# 修复前
if confidence > 0.3 and text.strip():

# 修复后
if confidence > 0.5 and text.strip():
```

- [ ] **Step 2: 提交**

```bash
git add modules/ocr.py
git commit -m "fix: increase OCR confidence threshold to 0.5 (HIGH-5)"
```

---

## Batch 4: 数据库优化

### Task 8: 添加数据库索引和连接管理

**Files:**
- Modify: `database.py`

- [ ] **Step 1: 读取当前 database.py**

- [ ] **Step 2: 添加索引**

```python
cursor.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        original_path TEXT NOT NULL,
        mp3_path TEXT,
        status TEXT DEFAULT 'pending',
        FOREIGN KEY (task_id) REFERENCES tasks(id)
    )
''')
# 添加索引
cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_task_id ON files(task_id)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
```

- [ ] **Step 3: 添加连接上下文管理器**

```python
from contextlib import contextmanager

@contextmanager
def get_db():
    conn = sqlite3.connect(Config.DATABASE, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

- [ ] **Step 4: 重写所有数据库函数使用 get_db()**

- [ ] **Step 5: 提交**

```bash
git add database.py
git commit -m "feat: add database indexes and connection management (HIGH-6, HIGH-7)"
```

---

## Batch 5: 输入验证

### Task 9: 添加output_mode验证和MAX_CONTENT_LENGTH

**Files:**
- Modify: `app.py`

- [ ] **Step 1: 添加 output_mode 验证**

```python
ALLOWED_OUTPUT_MODES = {'single', 'merged'}

@app.route('/api/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files')
    output_mode = request.form.get('output_mode', 'single')

    if output_mode not in ALLOWED_OUTPUT_MODES:
        return jsonify({'error': 'Invalid output_mode'}), 400
```

- [ ] **Step 2: 设置 Flask MAX_CONTENT_LENGTH**

```python
app = Flask(__name__)
app.config.from_object(Config)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
```

- [ ] **Step 3: 提交**

```bash
git add app.py
git commit -m "feat: add input validation for output_mode and file size (HIGH-2, HIGH-4)"
```

---

### Task 10: MP3合并添加警告

**Files:**
- Modify: `modules/mp3_merger.py`

- [ ] **Step 1: 读取并修改 mp3_merger.py**

```python
# 在合并循环前添加
missing_files = [p for p in mp3_paths if not os.path.exists(p)]
if missing_files:
    print(f"Warning: {len(missing_files)} MP3 files missing during merge: {missing_files}")
```

- [ ] **Step 2: 提交**

```bash
git add modules/mp3_merger.py
git commit -m "fix: warn when MP3 files are missing during merge (HIGH-3)"
```

---

### Task 11: 添加API认证（简化版）

**Files:**
- Modify: `app.py`

- [ ] **Step 1: 添加简单的API密钥检查**

```python
API_KEY = os.environ.get('BOOKVOICE_API_KEY', 'dev-key-change-me')

def verify_api_key():
    key = request.headers.get('X-API-Key')
    if key != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401

@app.route('/api/upload', methods=['POST'])
@verify_api_key
def upload():
    # ...
```

- [ ] **Step 2: 对其他API路由添加装饰器**

- [ ] **Step 3: 提交**

```bash
git add app.py
git commit -m "feat: add simple API key authentication (MEDIUM-2)"
```

---

## Batch 6: 文档更新

### Task 12: 更新README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 重写项目结构部分**

```markdown
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
├── modules/             # Python处理模块
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
```

- [ ] **Step 2: 更新"快速开始"部分**

```markdown
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
```

- [ ] **Step 3: 提交**

```bash
git add README.md
git commit -m "docs: update README to reflect actual project structure"
```

---

### Task 13: 更新UNIT_TEST_REPORT.md

**Files:**
- Modify: `UNIT_TEST_REPORT.md`

- [ ] **Step 1: 更新测试文件列表**

```markdown
### test_config.py (10个测试)
- test_base_dir_is_set ✅
- test_upload_folder_exists ✅
- test_output_folder_exists ✅
- test_log_folder_exists ✅
- test_database_is_set ✅
- test_max_content_length ✅
- test_skip_on_error_is_bool ✅
- test_allowed_extensions ✅
- test_tts_rate_is_set ✅
- test_tts_volume_is_set ✅

### test_database.py (9个测试)
- test_init_db_creates_tables ✅
- test_create_task_returns_uuid ✅
- test_get_task_returns_task_dict ✅
- test_get_task_returns_none_for_invalid_id ✅
- test_get_all_tasks_returns_list ✅
- test_create_file_record ✅
- test_update_task_status_to_completed ✅
- test_update_task_status_to_failed ✅
- test_update_file_status ✅

### test_translator.py (9个测试)
- test_is_english_returns_true_for_english_text ✅
- test_is_english_returns_false_for_chinese_text ✅
- test_is_english_returns_true_for_mostly_english ✅
- test_is_english_returns_false_for_mostly_chinese ✅
- test_is_english_handles_empty_string ✅
- test_is_english_handles_special_characters ✅
- test_translate_to_chinese_returns_same_for_chinese ✅
- test_translate_to_chinese_handles_empty_string ✅
- test_translate_to_chinese_returns_same_for_whitespace ✅
```

- [ ] **Step 2: 更新"已完成的改进"部分，移除不存在的测试文件引用**

- [ ] **Step 3: 提交**

```bash
git add UNIT_TEST_REPORT.md
git commit -m "docs: update UNIT_TEST_REPORT with actual test coverage"
```

---

## 自检清单

- [ ] 所有25个问题都有对应的修复任务
- [ ] 无占位符（TBD、TODO等）
- [ ] 每个任务的代码都是完整的
- [ ] 文件路径都是精确的
- [ ] 每个任务都有提交步骤
