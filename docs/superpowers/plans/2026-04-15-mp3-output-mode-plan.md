# MP3 Output Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Single/Merged 两种 MP3 输出模式，支持进度展示

**Architecture:**
- Single 模式：每个文档分片 TTS 后内部合并成一个 MP3，多文档打包 ZIP
- Merged 模式：所有文档各自生成 MP3 后，合并成一个大 MP3
- 进度通过 `/api/task/<task_id>/progress` 返回，已完成分片/总分片

**Tech Stack:** Python (Flask), pyttsx3, pydub, SQLite

---

## File Map

| File | Responsibility |
|------|----------------|
| `modules/task_queue.py` | 任务处理核心逻辑：OCR→翻译→分片TTS→文档内合并→文档间合并 |
| `modules/mp3_merger.py` | MP3 合并逻辑（已存在，无需修改） |
| `app.py` | 下载路由（判断 merged 模式）、进度路由（计算百分比） |

---

## Task 1: 修改 task_queue.py 核心处理逻辑

**Files:**
- Modify: `bookvoice/modules/task_queue.py`

**Current state:** 本地修改移除了分片和合并逻辑，需要恢复并增强

- [ ] **Step 1: 读取当前 task_queue.py**

```bash
cat bookvoice/modules/task_queue.py
```

确认当前代码状态（应该是移除了分片合并的简化版本）

- [ ] **Step 2: 编写新的 process_task 方法**

用以下完整实现替换现有的 `process_task` 方法（约第31-91行）：

```python
# 处理单个任务：OCR识别 → 翻译 → TTS生成MP3 → 合并（如需要）
def process_task(self, task_id: str):
    # 获取任务信息，任务不存在则直接返回
    task = get_task(task_id)
    if not task:
        return

    # 更新任务状态为处理中
    update_task_status(task_id, 'processing')
    files = get_files_by_task(task_id)
    output_mode = task.get('output_mode', 'single')

    # 创建输出目录
    output_dir = os.path.join(Config.OUTPUT_FOLDER, task_id)
    os.makedirs(output_dir, exist_ok=True)

    # 收集所有文档的MP3路径（用于merged模式）
    all_mp3_paths = []

    # 遍历任务下所有文件
    for file_record in files:
        try:
            file_path = file_record['original_path']
            ext = os.path.splitext(file_path)[1].lower()

            # 根据文件类型提取文字
            if ext in ['.png', '.jpg', '.jpeg']:
                # 图片文件 → OCR识别
                text = self.processors['ocr'].extract_structured_text(file_path)
            elif ext == '.pdf':
                # PDF文件 → PDF处理器提取
                text = self.processors['pdf'].extract_text(file_path)
            elif ext == '.docx':
                # Word文件 → Word处理器提取
                text = self.processors['word'].extract_text(file_path)
            else:
                raise ValueError(f"Unsupported file type: {ext}")

            # 翻译为中文
            translated_text = self.processors['translator'].translate_to_chinese(text)

            # 按段落分割文本（分片处理，避免超长文本导致TTS失败）
            paragraphs = [p.strip() for p in translated_text.split('\n\n') if p.strip()]

            # 更新文件总段落数
            update_file_segments(file_record['id'], len(paragraphs))

            # 进度回调函数
            def update_progress(processed_count):
                update_file_progress(file_record['id'], processed_count)

            # 串行TTS生成（Windows环境下pyttsx3并行有COM问题，使用串行）
            mp3_paths = self.processors['tts'].text_to_speech_segments_with_progress(
                paragraphs, output_dir, progress_callback=update_progress
            )

            # 文档内合并：将该文档的所有分片MP3合并成一个
            if mp3_paths:
                from .mp3_merger import merge_mp3_files
                doc_mp3 = os.path.join(output_dir, f'{file_record["id"]}.mp3')
                merge_mp3_files(mp3_paths, doc_mp3)
                all_mp3_paths.append(doc_mp3)
                update_file_status(file_record['id'], 'completed', doc_mp3)

            # 确保进度为100%
            update_file_progress(file_record['id'], len(paragraphs))

        except Exception as e:
            # 记录失败状态，错误处理
            update_file_status(file_record['id'], 'failed')
            if not Config.SKIP_ON_ERROR:
                raise
            self._log_error(task_id, file_record['original_path'], str(e))

    # merged模式：文档间合并
    if output_mode == 'merged' and len(all_mp3_paths) > 1:
        try:
            from .mp3_merger import merge_mp3_files
            merged_path = os.path.join(output_dir, 'merged.mp3')
            merge_mp3_files(all_mp3_paths, merged_path)
            # 更新第一个文件的mp3_path为合并后的路径
            if files:
                update_file_status(files[0]['id'], 'completed', merged_path)
        except Exception as e:
            self._log_error(task_id, 'merged.mp3', str(e))

    # 检查是否有成功处理的文件，更新任务最终状态
    files = get_files_by_task(task_id)
    any_success = any(f['status'] == 'completed' for f in files)

    if any_success:
        update_task_status(task_id, 'completed')
    else:
        update_task_status(task_id, 'failed')
```

- [ ] **Step 3: 验证语法**

```bash
cd bookvoice && python -m py_compile modules/task_queue.py && echo "Syntax OK"
```

- [ ] **Step 4: 提交**

```bash
git add modules/task_queue.py
git commit -m "feat: implement single/merged MP3 output mode with segment splitting

- Single mode: each document splits into segments, TTS, then merges internally
- Merged mode: all document MPs merged into one final MP3
- Progress tracking via file_segments and file_progress tables

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: 修改 app.py 下载路由（merged 模式支持）

**Files:**
- Modify: `bookvoice/app.py:100-120`

- [ ] **Step 1: 替换 download_task 方法**

将现有的 `download_task` 方法（约第100-120行）替换为：

```python
@app.route('/api/task/<task_id>/download', methods=['GET'])
@verify_api_key
def download_task(task_id):
    # GET /api/task/<task_id>/download - 下载任务生成的MP3文件
    # single模式：单文件直接返回，多文件打包ZIP
    # merged模式：返回合并后的单一MP3
    task = get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    output_dir = os.path.join(Config.OUTPUT_FOLDER, task_id)
    if not os.path.exists(output_dir):
        return jsonify({'error': 'Output not found'}), 404

    output_mode = task.get('output_mode', 'single')

    # merged模式：直接返回合并后的MP3
    if output_mode == 'merged':
        merged_path = os.path.join(output_dir, 'merged.mp3')
        if os.path.exists(merged_path):
            return send_file(merged_path, as_attachment=True)
        return jsonify({'error': 'Merged MP3 not found'}), 404

    # single模式：多文件打包ZIP
    files = get_files_by_task(task_id)
    mp3_files = [f['mp3_path'] for f in files if f['mp3_path'] and os.path.exists(f['mp3_path'])]
    if not mp3_files:
        return jsonify({'error': 'No MP3 files found'}), 404
    if len(mp3_files) == 1:
        return send_file(mp3_files[0], as_attachment=True)

    import shutil
    zip_path = os.path.join(Config.OUTPUT_FOLDER, f'{task_id}.zip')
    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', output_dir)
    return send_file(zip_path, as_attachment=True)
```

- [ ] **Step 2: 验证语法**

```bash
cd bookvoice && python -m py_compile app.py && echo "Syntax OK"
```

- [ ] **Step 3: 提交**

```bash
git add app.py
git commit -m "feat: support merged mode download returning single MP3

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: 修改 app.py 进度路由（添加 progress 百分比）

**Files:**
- Modify: `bookvoice/app.py:78-86`

- [ ] **Step 1: 替换 get_task_progress 方法**

将现有的 `get_task_progress` 方法替换为：

```python
@app.route('/api/task/<task_id>/progress', methods=['GET'])
@verify_api_key
def get_task_progress(task_id):
    # GET /api/task/<task_id>/progress - 获取任务处理进度
    from modules.database import get_task_progress as db_get_progress
    task = get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    data = db_get_progress(task_id)

    # 计算总体进度百分比：已完成分片数 / 总分片数
    total_segments = sum(f['total_segments'] for f in data['files'])
    processed_segments = sum(f['processed_segments'] for f in data['files'])

    if total_segments > 0:
        data['progress'] = int(processed_segments / total_segments * 100)
    else:
        data['progress'] = 0

    return jsonify(data), 200
```

- [ ] **Step 2: 验证语法**

```bash
cd bookvoice && python -m py_compile app.py && echo "Syntax OK"
```

- [ ] **Step 3: 提交**

```bash
git add app.py
git commit -m "feat: add progress percentage to task progress API

Progress calculated as: processed_segments / total_segments

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: 验证端到端流程

- [ ] **Step 1: 检查数据库表结构**

```bash
cd bookvoice && python -c "
from modules.database import init_db, get_db
init_db()
conn = get_db()
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(files)')
print('files table columns:')
for col in cursor.fetchall():
    print(f'  {col[1]} {col[2]}')
cursor.execute('PRAGMA table_info(tasks)')
print('tasks table columns:')
for col in cursor.fetchall():
    print(f'  {col[1]} {col[2]}')
conn.close()
"
```

确认 `files` 表有 `total_segments` 和 `processed_segments` 字段

- [ ] **Step 2: 检查 import 依赖**

```bash
cd bookvoice && python -c "
from modules.task_queue import TaskQueue
from modules.mp3_merger import merge_mp3_files
print('Imports OK')
"
```

- [ ] **Step 3: 启动服务测试**

```bash
cd bookvoice && python app.py
```

在另一个终端测试上传（需要准备测试文件）：

```bash
# 测试 single 模式
curl -X POST -H "X-API-Key: dev-key-change-me" \
  -F "files=@test.png" \
  -F "output_mode=single" \
  http://127.0.0.1:5000/api/upload

# 测试 merged 模式
curl -X POST -H "X-API-Key: dev-key-change-me" \
  -F "files=@test1.png" \
  -F "files=@test2.png" \
  -F "output_mode=merged" \
  http://127.0.0.1:5000/api/upload
```

- [ ] **Step 4: 检查进度 API**

```bash
curl -H "X-API-Key: dev-key-change-me" \
  http://127.0.0.1:5000/api/task/<task_id>/progress
```

确认返回包含 `progress` 字段

- [ ] **Step 5: 检查下载**

```bash
# single 模式：应返回单个MP3或ZIP
curl -H "X-API-Key: dev-key-change-me" \
  http://127.0.0.1:5000/api/task/<task_id>/download \
  -o single_download.zip

# merged 模式：应返回单个MP3
curl -H "X-API-Key: dev-key-change-me" \
  http://127.0.0.1:5000/api/task/<task_id>/download \
  -o merged_download.mp3
```

---

## Spec Coverage Check

| 设计要求 | 实现位置 |
|----------|----------|
| Single 模式分片 TTS | Task 1: `text_to_speech_segments_with_progress` |
| Single 模式文档内合并 | Task 1: `merge_mp3_files(mp3_paths, doc_mp3)` |
| Single 模式 ZIP 下载 | Task 2: `shutil.make_archive` |
| Merged 模式文档间合并 | Task 1: `merge_mp3_files(all_mp3_paths, merged.mp3)` |
| Merged 模式直接下载 MP3 | Task 2: `output_mode == 'merged'` 分支 |
| 进度百分比计算 | Task 3: `progress` 字段 |

## Placeholder Scan

- 无 "TBD"、"TODO" 占位符
- 无 "Add appropriate error handling" 等模糊描述
- 所有代码步骤包含完整实现

## Type Consistency

- `task_queue.py` 使用 `task.get('output_mode', 'single')` — 与 `database.py` 中 `output_mode TEXT DEFAULT 'single'` 一致
- `app.py` 下载路由中 `output_mode` 判断与设计文档一致
- 进度计算公式与设计文档一致
