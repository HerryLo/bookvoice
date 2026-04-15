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
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        ''')
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
            'INSERT INTO files (task_id, original_path) VALUES (?, ?)',
            (task_id, original_path)
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