import pytest
import sys
import os
import tempfile
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Config before importing database
class MockConfig:
    BASE_DIR = tempfile.gettempdir()
    DATABASE = os.path.join(tempfile.gettempdir(), 'test_bookvoice.db')


class TestDatabase:
    """Test Database module"""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Create a test database before each test"""
        # Import here to allow mocking Config first
        import importlib
        import config
        importlib.reload(config)

        # Patch Config in database module
        import database
        database.Config = MockConfig

        # Create tables
        database.init_db()

        yield

        # Cleanup: close connection and remove test db
        try:
            os.remove(MockConfig.DATABASE)
        except:
            pass

    def test_init_db_creates_tables(self):
        """Test that init_db creates tasks and files tables"""
        conn = sqlite3.connect(MockConfig.DATABASE)
        cursor = conn.cursor()

        # Check tasks table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        assert cursor.fetchone() is not None

        # Check files table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
        assert cursor.fetchone() is not None

        conn.close()

    def test_create_task_returns_uuid(self):
        """Test that create_task returns a valid UUID string"""
        from database import create_task

        task_id = create_task('test_file.pdf', 'single')

        assert task_id is not None
        assert isinstance(task_id, str)
        assert len(task_id) == 36  # UUID format

    def test_get_task_returns_task_dict(self):
        """Test that get_task returns correct task data"""
        from database import create_task, get_task

        task_id = create_task('test.pdf', 'single')
        task = get_task(task_id)

        assert task is not None
        assert task['id'] == task_id
        assert task['filename'] == 'test.pdf'
        assert task['status'] == 'pending'
        assert task['output_mode'] == 'single'

    def test_get_task_returns_none_for_invalid_id(self):
        """Test that get_task returns None for non-existent task"""
        from database import get_task

        task = get_task('non-existent-id')
        assert task is None

    def test_get_all_tasks_returns_list(self):
        """Test that get_all_tasks returns a list"""
        from database import create_task, get_all_tasks

        # Create multiple tasks
        create_task('file1.pdf', 'single')
        create_task('file2.pdf', 'single')

        tasks = get_all_tasks()

        assert isinstance(tasks, list)
        assert len(tasks) >= 2

    def test_create_file_record(self):
        """Test that create_file_record creates a file record"""
        from database import create_task, create_file_record, get_files_by_task

        task_id = create_task('test.pdf', 'single')
        file_id = create_file_record(task_id, '/path/to/file.pdf')

        assert file_id is not None
        assert isinstance(file_id, int)

        files = get_files_by_task(task_id)
        assert len(files) == 1
        assert files[0]['original_path'] == '/path/to/file.pdf'

    def test_update_task_status_to_completed(self):
        """Test updating task status to completed"""
        from database import create_task, update_task_status, get_task

        task_id = create_task('test.pdf', 'single')
        update_task_status(task_id, 'completed')

        task = get_task(task_id)
        assert task['status'] == 'completed'
        assert task['completed_at'] is not None

    def test_update_task_status_to_failed(self):
        """Test updating task status to failed with error message"""
        from database import create_task, update_task_status, get_task

        task_id = create_task('test.pdf', 'single')
        update_task_status(task_id, 'failed', 'Test error message')

        task = get_task(task_id)
        assert task['status'] == 'failed'
        assert task['error_msg'] == 'Test error message'

    def test_update_file_status(self):
        """Test updating file status with mp3 path"""
        from database import create_task, create_file_record, update_file_status, get_files_by_task

        task_id = create_task('test.pdf', 'single')
        file_id = create_file_record(task_id, '/path/to/file.pdf')

        update_file_status(file_id, 'completed', '/path/to/output.mp3')

        files = get_files_by_task(task_id)
        assert files[0]['status'] == 'completed'
        assert files[0]['mp3_path'] == '/path/to/output.mp3'
