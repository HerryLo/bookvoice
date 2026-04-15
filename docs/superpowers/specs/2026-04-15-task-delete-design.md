# 任务删除功能设计

## 概述

为 BookVoice 添加任务和文件的删除功能，支持删除整个任务或单个文件，同时清理物理文件和数据库记录。

## 需求

1. 删除整个任务（只能删除 completed/failed 状态的任务）
2. 删除单个文件（删除后如果任务下没有文件了，同时删除任务）
3. 删除前需要二次确认

## API 设计

### 1. DELETE /api/task/<task_id>

删除整个任务。

**请求**
- Header: `X-API-Key: <api_key>`

**业务逻辑**
1. 检查任务存在
2. 检查任务状态必须是 `completed` 或 `failed`（禁止删除 `pending`/`processing` 状态）
3. 删除 `storage/uploads/<task_id>/` 目录及所有文件
4. 删除 `storage/outputs/<task_id>/` 目录及所有文件
5. 从数据库删除 task 记录和关联的 file 记录

**响应**
- 200: `{ "message": "Task deleted" }`
- 400: `{ "error": "Cannot delete task in processing" }`（任务正在处理中）
- 404: `{ "error": "Task not found" }`

### 2. DELETE /api/file/<file_id>

删除单个文件。

**请求**
- Header: `X-API-Key: <api_key>`

**业务逻辑**
1. 检查文件记录存在
2. 获取关联的任务信息
3. 检查任务状态必须是 `completed` 或 `failed`
4. 删除上传的物理文件（如果存在）
5. 删除生成的 MP3 文件（如果存在）
6. 从数据库删除 file 记录
7. 检查该任务是否还有其他文件，如果没有则删除整个任务

**响应**
- 200: `{ "message": "File deleted" }`
- 400: `{ "error": "Cannot delete file from task in processing" }`
- 404: `{ "error": "File not found" }`

## 数据库变更

### 新增函数 (modules/database.py)

```python
def get_file(file_id):
    """获取单个文件记录"""
    with get_db_cursor() as cursor:
        cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def delete_file(file_id):
    """删除单个文件及其物理文件"""
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

def delete_task(task_id):
    """删除任务及其所有文件和目录"""
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

## 前端变更

### api/index.js

```javascript
export const deleteTask = (taskId) => api.delete(`/task/${taskId}`)
export const deleteFile = (fileId) => api.delete(`/file/${fileId}`)
```

### TaskList.vue

**数据展开**
- 每行添加展开详情，显示该任务下的所有文件列表
- 文件列表每行有删除按钮

**操作列变更**
- 下载按钮、重试按钮（现有）
- 新增红色"删除任务"按钮

**删除确认**
- 使用 `ElMessageBox.confirm` 弹出确认对话框
- 消息："确定删除吗？此操作不可恢复"
- 类型：warning
- 确认后执行删除

**UI 示例**
```
| 文件名 | 状态 | 操作 |
|--------|------|------|
| a.jpg | 已完成 | [下载] [删除] |
| b.pdf | 已完成 | [下载] [删除] |
```

## 文件结构

```
bookvoice/
├── app.py                 # 新增 DELETE /api/task/<id>, DELETE /api/file/<id>
├── config.py
├── frontend/
│   └── src/
│       ├── api/index.js   # 新增 deleteTask, deleteFile
│       └── views/
│           └── TaskList.vue  # 添加删除按钮和确认对话框
├── modules/
│   ├── database.py        # 新增 delete_task, delete_file, get_file
│   ├── task_queue.py
│   └── ...
```

## 安全考虑

- 所有删除操作需要 API 认证（X-API-Key）
- 只能删除已完成或失败的任务/文件，防止数据不一致
- 删除物理文件使用 `os.remove` 和 `shutil.rmtree`，确保文件被彻底删除
