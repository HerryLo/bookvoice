# 一键清空功能设计

## 背景

用户需要快速清空任务列表和日志文件，减少手动逐个删除的繁琐操作。

## 功能需求

### 任务列表清空

**后端 API：**
- `DELETE /api/tasks` — 清空所有已完成/失败的任务
  - 删除数据库中 tasks 表记录
  - 删除数据库中对应的 files 表记录
  - 删除上传文件（原文件）
  - 删除生成的 MP3 文件（outputs 目录）

**前端：**
- TaskList.vue 标题栏添加"清空全部"按钮
- 点击后弹出确认框，确认后执行清空
- 清空成功后刷新列表

### 日志清空

**后端 API：**
- `DELETE /api/logs` — 清空所有日志文件
  - 删除 `logs/error_*.log` 所有文件

**前端：**
- Logs.vue 标题栏添加"清空全部"按钮
- 点击后弹出确认框，确认后执行清空
- 清空成功后刷新列表

## 数据流

### 任务清空流程

```
前端：点击"清空全部" → 确认框 → DELETE /api/tasks
                                          ↓
后端：获取所有 completed/failed 任务
    → 删除每个任务的 files 记录
    → 删除每个任务的上传文件（storage/uploads/<task_id>/）
    → 删除每个任务的输出文件（storage/outputs/<task_id>/）
    → 删除 tasks 表记录
    → 返回成功
                                          ↓
前端：刷新列表
```

### 日志清空流程

```
前端：点击"清空全部" → 确认框 → DELETE /api/logs
                                          ↓
后端：遍历 logs/ 目录
    → 删除所有 error_*.log 文件
    → 返回成功
                                          ↓
前端：刷新列表
```

## 修改文件

### `app.py`

新增两个 API 端点：

```python
# ---------- 工具相关 ----------

@app.route('/api/tasks', methods=['DELETE'])
@verify_api_key
def clear_tasks():
    # DELETE /api/tasks - 清空所有已完成/失败的任务
    # 删除数据库记录、上传文件、生成的MP3
    conn = get_db()
    cursor = conn.cursor()

    # 获取所有已完成/失败的任务
    cursor.execute("SELECT id FROM tasks WHERE status IN ('completed', 'failed')")
    tasks = cursor.fetchall()

    for (task_id,) in tasks:
        # 删除上传文件
        upload_dir = os.path.join(Config.UPLOAD_FOLDER, task_id)
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)
        # 删除输出文件
        output_dir = os.path.join(Config.OUTPUT_FOLDER, task_id)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        # 删除数据库文件记录
        cursor.execute('DELETE FROM files WHERE task_id = ?', (task_id,))

    # 删除任务记录
    cursor.execute("DELETE FROM tasks WHERE status IN ('completed', 'failed')")
    conn.commit()
    conn.close()

    return jsonify({'message': f'已清空 {len(tasks)} 个任务'}), 200

@app.route('/api/logs', methods=['DELETE'])
@verify_api_key
def clear_logs():
    # DELETE /api/logs - 清空所有错误日志
    if not os.path.exists(Config.LOG_FOLDER):
        return jsonify({'message': '日志目录为空'}), 200

    deleted_count = 0
    for filename in os.listdir(Config.LOG_FOLDER):
        if filename.startswith('error_'):
            log_path = os.path.join(Config.LOG_FOLDER, filename)
            os.remove(log_path)
            deleted_count += 1

    return jsonify({'message': f'已清空 {deleted_count} 个日志文件'}), 200
```

### `frontend/src/api/index.js`

新增 API 方法：

```javascript
export const clearTasks = () => api.delete('/tasks')

export const clearLogs = () => api.delete('/logs')
```

### `frontend/src/views/TaskList.vue`

在刷新按钮旁添加"清空全部"按钮：

```vue
<el-button @click="refreshTasks" :loading="loading">刷新</el-button>
<el-button @click="handleClearAll" type="danger" plain>清空全部</el-button>
```

新增方法：

```javascript
const handleClearAll = async () => {
  try {
    await ElMessageBox.confirm(
      '确定清空所有已完成/失败的任务吗？此操作不可恢复',
      '清空确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await clearTasks()
    ElMessage.success('清空成功')
    refreshTasks()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('清空失败')
    }
  }
}
```

### `frontend/src/views/Logs.vue`

在刷新按钮旁添加"清空全部"按钮：

```vue
<el-button @click="loadLogs" :loading="loading">刷新日志</el-button>
<el-button @click="handleClearAll" type="danger" plain>清空全部</el-button>
```

新增方法：

```javascript
import { clearLogs } from '../api'

const handleClearAll = async () => {
  try {
    await ElMessageBox.confirm(
      '确定清空所有日志吗？此操作不可恢复',
      '清空确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await clearLogs()
    ElMessage.success('清空成功')
    loadLogs()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('清空失败')
    }
  }
}
```

## 边界情况

| 情况 | 处理方式 |
|------|----------|
| 无任务可清空 | 返回成功，前端显示"已清空 0 个任务" |
| 部分文件已删除 | 跳过不存在的文件，继续删除其他文件 |
| 任务正在处理中 | 保留 processing/pending 状态的任务 |
| 日志目录为空 | 返回成功，前端显示"日志目录为空" |

## 测试要点

1. 清空任务 → 确认 tasks 表和 files 表记录已删除
2. 清空任务 → 确认 storage/uploads/<task_id> 已删除
3. 清空任务 → 确认 storage/outputs/<task_id> 已删除
4. 清空日志 → 确认 logs/ 目录下 error_*.log 已删除
5. 有处理中任务时清空 → 确认 processing 任务被保留
6. 清空后前端列表正确刷新
