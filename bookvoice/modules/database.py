import os
import sqlite3
import uuid
from datetime import datetime
from contextlib import contextmanager
from config import Config

def get_db():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db_cursor():
    conn = get_db()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db_cursor() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                error_msg TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                output_mode TEXT DEFAULT 'single'
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                original_path TEXT NOT NULL,
                mp3_path TEXT,
                status TEXT DEFAULT 'pending',
                processed_segments INTEGER DEFAULT 0,
                total_segments INTEGER DEFAULT 0,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        ''')
        # 迁移：确保新字段存在（兼容已有数据库）
        try:
            cursor.execute('ALTER TABLE files ADD COLUMN processed_segments INTEGER DEFAULT 0')
        except:
            pass  # 字段已存在
        try:
            cursor.execute('ALTER TABLE files ADD COLUMN total_segments INTEGER DEFAULT 0')
        except:
            pass  # 字段已存在
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_task_id ON files(task_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')

def create_task(filename: str, output_mode: str = 'single') -> str:
    task_id = str(uuid.uuid4())
    with get_db_cursor() as cursor:
        cursor.execute(
            'INSERT INTO tasks (id, filename, output_mode) VALUES (?, ?, ?)',
            (task_id, filename, output_mode)
        )
    return task_id

def create_file_record(task_id: str, original_path: str) -> int:
    with get_db_cursor() as cursor:
        cursor.execute(
            'INSERT INTO files (task_id, original_path, processed_segments, total_segments) VALUES (?, ?, ?, ?)',
            (task_id, original_path, 0, 0)
        )
        return cursor.lastrowid

def update_task_status(task_id: str, status: str, error_msg: str = None):
    with get_db_cursor() as cursor:
        if status == 'completed':
            cursor.execute(
                'UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?',
                (status, datetime.now().isoformat(), task_id)
            )
        else:
            cursor.execute(
                'UPDATE tasks SET status = ?, error_msg = ? WHERE id = ?',
                (status, error_msg, task_id)
            )

def update_file_status(file_id: int, status: str, mp3_path: str = None):
    with get_db_cursor() as cursor:
        if mp3_path:
            cursor.execute(
                'UPDATE files SET status = ?, mp3_path = ? WHERE id = ?',
                (status, mp3_path, file_id)
            )
        else:
            cursor.execute(
                'UPDATE files SET status = ? WHERE id = ?',
                (status, file_id)
            )

def get_task(task_id: str) -> dict:
    with get_db_cursor() as cursor:
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_tasks() -> list:
    with get_db_cursor() as cursor:
        cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
        return [dict(row) for row in cursor.fetchall()]

def get_files_by_task(task_id: str) -> list:
    with get_db_cursor() as cursor:
        cursor.execute('SELECT * FROM files WHERE task_id = ?', (task_id,))
        return [dict(row) for row in cursor.fetchall()]

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