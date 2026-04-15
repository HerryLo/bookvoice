# 任务删除功能实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为任务列表添加删除功能，支持删除整个任务或单个文件

**Architecture:** 后端添加 delete_task/delete_file 数据库函数和对应API，前端TaskList.vue添加删除按钮和确认对话框

**Tech Stack:** Python/Flask, SQLite, Vue3/Element Plus

---

## 文件结构

```
bookvoice/
├── modules/
│   └── database.py     # 新增 delete_task, delete_file, get_file
├── app.py              # 新增 DELETE /api/task/<id>, DELETE /api/file/<id>
├── frontend/
│   └── src/
│       ├── api/index.js   # 新增 deleteTask, deleteFile
│       └── views/
│           └── TaskList.vue  # 添加删除按钮
```

---

## Task 1: 添加数据库删除函数

**Files:**
- Modify: `modules/database.py`

- [ ] **Step 1: 读取当前 database.py 末尾**

```python
# 查看现有函数列表
```

- [ ] **Step 2: 在文件末尾添加新函数**

```python
def get_file(file_id: int) -> dict:
    """获取单个文件记录"""
    with get_db_cursor() as cursor:
        cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def delete_file(file_id: int) -> bool:
    """删除单个文件及其物理文件"""
    import shutil
    file_record = get_file(file_id)
    if not file_record:
        return False

    # 删除上传的原文件
    if file_record['original_path'] and os.path.exists(file_record['original_path']):
        os.remove(file_record['original_path'])

    # 删除生成的MP3
    if file_record['mp3_path'] and os.path.exists(file_record['mp3_path']):
        os.remove(file_record['mp3_path'])

    # 从数据库删除记录
    with get_db_cursor() as cursor:
        cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))

    # 检查任务是否还有其他文件
    remaining = get_files_by_task(file_record['task_id'])
    if not remaining:
        delete_task(file_record['task_id'])

    return True

def delete_task(task_id: str) -> bool:
    """删除任务及其所有文件和目录"""
    import shutil
    task = get_task(task_id)
    if not task:
        return False

    # 删除上传目录
    upload_dir = os.path.join(Config.UPLOAD_FOLDER, task_id)
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)

    # 删除输出目录
    output_dir = os.path.join(Config.OUTPUT_FOLDER, task_id)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    # 删除数据库记录（先删文件再删任务，因为有外键）
    with get_db_cursor() as cursor:
        cursor.execute('DELETE FROM files WHERE task_id = ?', (task_id,))
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))

    return True
```

- [ ] **Step 3: 验证导入正常**

```bash
cd D:/dev/Claude\ Code\ Test/bookvoice && py -c "from modules.database import delete_task, delete_file, get_file; print('ok')"
```

- [ ] **Step 4: 提交**

```bash
git add modules/database.py
git commit -m "feat: add delete_task and delete_file to database module"
```

---

## Task 2: 添加后端API端点

**Files:**
- Modify: `app.py`

- [ ] **Step 1: 添加 delete_task, delete_file 到 import**

```python
from modules.database import init_db, create_task, create_file_record, get_all_tasks, get_task, get_files_by_task, delete_task, delete_file
```

- [ ] **Step 2: 在 retry_task 路由后添加新路由**

```python
@app.route('/api/task/<task_id>', methods=['DELETE'])
@verify_api_key
def delete_task_api(task_id):
    task = get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    if task['status'] not in ('completed', 'failed'):
        return jsonify({'error': 'Cannot delete task in processing'}), 400

    delete_task(task_id)
    return jsonify({'message': 'Task deleted'}), 200

@app.route('/api/file/<int:file_id>', methods=['DELETE'])
@verify_api_key
def delete_file_api(file_id):
    from modules.database import get_file
    file_record = get_file(file_id)
    if not file_record:
        return jsonify({'error': 'File not found'}), 404

    task = get_task(file_record['task_id'])
    if not task or task['status'] not in ('completed', 'failed'):
        return jsonify({'error': 'Cannot delete file from task in processing'}), 400

    delete_file(file_id)
    return jsonify({'message': 'File deleted'}), 200
```

- [ ] **Step 3: 测试API导入**

```bash
cd D:/dev/Claude\ Code\ Test/bookvoice && py -c "from app import app; print('ok')"
```

- [ ] **Step 4: 提交**

```bash
git add app.py
git commit -m "feat: add DELETE /api/task/<id> and DELETE /api/file/<id> endpoints"
```

---

## Task 3: 前端API函数

**Files:**
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: 添加删除API函数**

在文件末尾添加：

```javascript
export const deleteTask = (taskId) => api.delete(`/task/${taskId}`)

export const deleteFile = (fileId) => api.delete(`/file/${fileId}`)
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/api/index.js
git commit -m "feat: add deleteTask and deleteFile API functions"
```

---

## Task 4: 前端删除按钮

**Files:**
- Modify: `frontend/src/views/TaskList.vue`

- [ ] **Step 1: 添加删除方法和确认对话框**

在 `<script setup>` 中：

```javascript
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTasks, downloadTask, retryTask as retryTaskApi, deleteTask as deleteTaskApi, deleteFile as deleteFileApi } from '../api'

// 在 refreshTasks 函数后添加：

const handleDeleteTask = async (taskId) => {
  try {
    await ElMessageBox.confirm(
      '确定删除吗？此操作不可恢复',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await deleteTaskApi(taskId)
    ElMessage.success('删除成功')
    refreshTasks()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}
```

- [ ] **Step 2: 在操作列添加删除按钮**

修改操作列模板，在重试按钮后添加：

```html
<el-button
  v-if="row.status === 'failed'"
  type="warning"
  size="small"
  @click="retryTask(row.id)"
>重试</el-button>
<el-button
  v-if="row.status === 'completed' || row.status === 'failed'"
  type="danger"
  size="small"
  @click="handleDeleteTask(row.id)"
>删除</el-button>
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/TaskList.vue
git commit -m "feat: add delete button to TaskList with confirmation dialog"
```

---

## 自检清单

- [ ] delete_task 和 delete_file 函数已添加
- [ ] DELETE /api/task/<id> 端点已添加
- [ ] DELETE /api/file/<id> 端点已添加
- [ ] 前端 deleteTask, deleteFile API 函数已添加
- [ ] TaskList.vue 添加了删除按钮和确认对话框
- [ ] 所有更改已提交
