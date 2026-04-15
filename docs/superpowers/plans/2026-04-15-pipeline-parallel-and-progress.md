# 增量流水线并行 + 进度展示 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现增量流水线并行处理大文档，翻译和TTS分段交叉执行，实时展示处理进度

**Architecture:** 同步串行流程改为增量流水线并行，后端实时更新进度到数据库，前端通过轮询获取并展示进度

**Tech Stack:** Python/Flask/SQLite, Vue3/Element Plus, ThreadPoolExecutor

---

## 文件结构

```
bookvoice/
├── app.py                           # 修改：新增 GET /api/task/<id>/progress
├── modules/
│   ├── database.py                 # 修改：新增字段和函数
│   ├── task_queue.py               # 修改：增量流水线逻辑
│   ├── translator.py               # 修改：增量翻译方法
│   └── tts.py                      # 修改：并行TTS生成
├── frontend/src/
│   ├── api/index.js                # 修改：新增 getTaskProgress
│   └── views/
│       └── TaskList.vue            # 修改：显示进度条
└── tests/
    └── test_database.py            # 修改：新增进度相关测试
```

---

## Task 1: 数据库字段和函数

**Files:**
- Modify: `modules/database.py`
- Modify: `tests/test_database.py`

- [ ] **Step 1: 读取 database.py 末尾**

```bash
tail -30 modules/database.py
```

- [ ] **Step 2: 添加新字段和函数**

在 `modules/database.py` 末尾添加：

```python
# ---------- 进度相关 ----------

def update_file_segments(file_id: int, total_segments: int):
    # 更新文件总段落数
    with get_db_cursor() as cursor:
        cursor.execute(
            'UPDATE files SET total_segments = ? WHERE id = ?',
            (total_segments, file_id)
        )

def update_file_progress(file_id: int, processed_segments: int):
    # 更新文件已处理段落数
    with get_db_cursor() as cursor:
        cursor.execute(
            'UPDATE files SET processed_segments = ? WHERE id = ?',
            (processed_segments, file_id)
        )

def get_task_progress(task_id: str) -> dict:
    # 获取任务进度信息
    task = get_task(task_id)
    if not task:
        return None
    files = get_files_by_task(task_id)
    return {
        'task_id': task_id,
        'status': task['status'],
        'files': [
            {
                'id': f['id'],
                'original_path': f['original_path'],
                'total_segments': f['total_segments'] or 0,
                'processed_segments': f['processed_segments'] or 0,
                'status': f['status']
            }
            for f in files
        ]
    }
```

- [ ] **Step 3: 修改 create_file_record 函数**

找到 `create_file_record` 函数，在 RETURN 语句前添加：

```python
cursor.execute(
    'INSERT INTO files (task_id, original_path, mp3_path, status, processed_segments, total_segments) VALUES (?, ?, ?, ?, ?, ?)',
    (task_id, original_path, '', 'pending', 0, 0)
)
```

- [ ] **Step 4: 验证导入**

```bash
cd D:/dev/Claude\ Code\ Test/bookvoice && py -c "from modules.database import update_file_progress, get_task_progress, update_file_segments; print('ok')"
```

- [ ] **Step 5: 提交**

```bash
git add modules/database.py && git commit -m "feat: add progress tracking functions to database module

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: 数据库表结构变更

**Files:**
- Modify: `modules/database.py`

- [ ] **Step 1: 读取 database.py 的 init_db 函数**

找到 `init_db` 函数中的 `CREATE TABLE IF NOT EXISTS files` 部分

- [ ] **Step 2: 修改 files 表创建语句**

在 `CREATE TABLE IF NOT EXISTS files` 中添加新字段：

```sql
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    original_path TEXT NOT NULL,
    mp3_path TEXT DEFAULT '',
    status TEXT DEFAULT 'pending',
    processed_segments INTEGER DEFAULT 0,
    total_segments INTEGER DEFAULT 0,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
)
```

- [ ] **Step 3: 迁移现有数据库**

在 `init_db` 函数末尾添加：

```python
# 迁移：确保新字段存在
with get_db_cursor() as cursor:
    try:
        cursor.execute('ALTER TABLE files ADD COLUMN processed_segments INTEGER DEFAULT 0')
    except:
        pass  # 字段已存在
    try:
        cursor.execute('ALTER TABLE files ADD COLUMN total_segments INTEGER DEFAULT 0')
    except:
        pass  # 字段已存在
```

- [ ] **Step 4: 验证数据库变更**

```bash
cd D:/dev/Claude\ Code\ Test/bookvoice && py -c "from modules.database import init_db; init_db(); print('ok')"
```

- [ ] **Step 5: 提交**

```bash
git add modules/database.py && git commit -m "feat: add processed_segments and total_segments columns to files table

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: 后端进度API

**Files:**
- Modify: `app.py`

- [ ] **Step 1: 读取 app.py 末尾 API 路由部分**

```bash
tail -30 app.py
```

- [ ] **Step 2: 在任务相关路由部分添加新API**

在 `get_task_detail` 函数后添加：

```python
@app.route('/api/task/<task_id>/progress', methods=['GET'])
@verify_api_key
def get_task_progress(task_id):
    # GET /api/task/<task_id>/progress - 获取任务处理进度
    from modules.database import get_task_progress as db_get_progress
    task = get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(db_get_progress(task_id)), 200
```

- [ ] **Step 3: 验证导入**

```bash
cd D:/dev/Claude\ Code\ Test/bookvoice && py -c "from app import app; print('ok')"
```

- [ ] **Step 4: 提交**

```bash
git add app.py && git commit -m "feat: add GET /api/task/<id>/progress endpoint

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: 前端API函数

**Files:**
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: 读取 api/index.js**

```bash
cat frontend/src/api/index.js
```

- [ ] **Step 2: 添加 getTaskProgress 函数**

在文件末尾（`export default api` 之前）添加：

```javascript
export const getTaskProgress = (taskId) => api.get(`/task/${taskId}/progress`)
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/api/index.js && git commit -m "feat: add getTaskProgress API function

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: 前端进度显示

**Files:**
- Modify: `frontend/src/views/TaskList.vue`

- [ ] **Step 1: 修改 api 导入**

```javascript
import { getTasks, downloadTask, retryTask as retryTaskApi, deleteTask as deleteTaskApi, getTaskProgress } from '../api'
```

- [ ] **Step 2: 修改表格列**

在操作列之前添加进度列：

```vue
<el-table-column prop="progress" label="进度" width="150">
  <template #default="{ row }">
    <el-progress
      v-if="row.status === 'processing'"
      :percentage="row.total_segments > 0 ? Math.round(row.processed_segments / row.total_segments * 100) : 0"
      :text-inside="true"
      :stroke-width="12"
    />
    <el-tag v-else :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
  </template>
</el-table-column>
```

- [ ] **Step 3: 修改 refreshTasks 获取进度**

```javascript
const refreshTasks = async () => {
  loading.value = true
  try {
    const { data } = await getTasks()
    // 获取每个任务的进度
    const tasksWithProgress = await Promise.all(
      data.map(async (task) => {
        if (task.status === 'processing' || task.status === 'pending') {
          try {
            const { data: progress } = await getTaskProgress(task.id)
            return { ...task, ...progress }
          } catch {
            return task
          }
        }
        return task
      })
    )
    tasks.value = tasksWithProgress
  } catch (e) {
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/TaskList.vue && git commit -m "feat: add progress bar display to TaskList

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: TTS并行生成

**Files:**
- Modify: `modules/tts.py`

- [ ] **Step 1: 读取 tts.py**

```bash
cat modules/tts.py
```

- [ ] **Step 2: 修改导入**

在文件顶部添加：

```python
from concurrent.futures import ThreadPoolExecutor
from config import Config
```

- [ ] **Step 3: 添加并行生成方法**

在类末尾添加：

```python
def text_to_speech_parallel(self, segments: list, output_dir: str, progress_callback=None) -> list:
    # 多线程并行生成MP3
    mp3_paths = []
    max_workers = getattr(Config, 'TTS_PARALLEL_WORKERS', 3)

    def generate_single(segment, output_path):
        if segment.strip():
            self.text_to_speech(segment, output_path)
            return output_path
        return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i, segment in enumerate(segments):
            output_path = os.path.join(output_dir, f'segment_{i:04d}.mp3')
            future = executor.submit(generate_single, segment, output_path)
            futures.append((future, output_path, i + 1))

        for future, path, processed_count in futures:
            result = future.result()
            if result:
                mp3_paths.append(path)
            if progress_callback:
                progress_callback(processed_count)

    return mp3_paths
```

- [ ] **Step 4: 验证导入**

```bash
cd D:/dev/Claude\ Code\ Test/bookvoice && py -c "from modules.tts import TTSProcessor; t = TTSProcessor(); print('ok')"
```

- [ ] **Step 5: 提交**

```bash
git add modules/tts.py && git commit -m "feat: add text_to_speech_parallel method for concurrent TTS generation

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 7: task_queue流水线整合

**Files:**
- Modify: `modules/task_queue.py`

- [ ] **Step 1: 读取 task_queue.py 开头导入部分**

- [ ] **Step 2: 添加新的导入**

```python
from modules.database import update_file_progress, update_file_segments
```

- [ ] **Step 3: 修改 process_task 中的文件处理循环**

找到 `for file_record in files:` 循环，修改为：

```python
for file_record in files:
    try:
        file_path = file_record['original_path']
        ext = os.path.splitext(file_path)[1].lower()

        # 根据文件类型提取文字
        if ext in ['.png', '.jpg', '.jpeg']:
            text = self.processors['ocr'].extract_structured_text(file_path)
        elif ext == '.pdf':
            text = self.processors['pdf'].extract_text(file_path)
        elif ext == '.docx':
            text = self.processors['word'].extract_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        # 翻译为中文
        translated_text = self.processors['translator'].translate_to_chinese(text)

        # 按段落分割文本
        paragraphs = [p.strip() for p in translated_text.split('\n\n') if p.strip()]

        # 更新总段落数
        update_file_segments(file_record['id'], len(paragraphs))

        # 进度回调函数
        def update_progress(processed_count):
            update_file_progress(file_record['id'], processed_count)

        # 并行TTS生成
        mp3_paths = self.processors['tts'].text_to_speech_parallel(
            paragraphs, output_dir, progress_callback=update_progress
        )

        # 更新文件状态
        if mp3_paths:
            if output_mode == 'merged':
                all_mp3_paths.extend(mp3_paths)
                update_file_status(file_record['id'], 'completed', mp3_paths[0])
            else:
                main_mp3 = mp3_paths[0]
                update_file_status(file_record['id'], 'completed', main_mp3)

        # 确保进度为100%
        update_file_progress(file_record['id'], len(paragraphs))

    except Exception as e:
        update_file_status(file_record['id'], 'failed')
        if not Config.SKIP_ON_ERROR:
            raise
        self._log_error(task_id, file_record['original_path'], str(e))
```

- [ ] **Step 4: 验证导入**

```bash
cd D:/dev/Claude\ Code\ Test/bookvoice && py -c "from modules.task_queue import TaskQueue; print('ok')"
```

- [ ] **Step 5: 提交**

```bash
git add modules/task_queue.py && git commit -m "feat: integrate parallel TTS and progress tracking into task pipeline

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 8: 前端重新构建

**Files:**
- Modify: `frontend/package.json` (构建输出)

- [ ] **Step 1: 构建前端**

```bash
cd frontend && npm run build
```

- [ ] **Step 2: 验证构建输出**

检查 `../static/assets/` 目录下有新的 JS 和 CSS 文件

- [ ] **Step 3: 提交**

```bash
git add static/ && git commit -m "build: rebuild frontend with progress display

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 自检清单

- [ ] 数据库新增字段 processed_segments, total_segments
- [ ] 新增 update_file_progress, get_task_progress, update_file_segments 函数
- [ ] GET /api/task/<id>/progress API 端点
- [ ] 前端 getTaskProgress API 函数
- [ ] TaskList.vue 显示进度条
- [ ] TTS 并行生成方法 text_to_speech_parallel
- [ ] task_queue 整合进度更新和并行TTS
- [ ] 前端重新构建
- [ ] 所有更改已提交
