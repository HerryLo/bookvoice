from flask import Flask, render_template, request, jsonify, send_file
import os
import uuid
from werkzeug.utils import secure_filename
from config import Config
from database import init_db, create_task, create_file_record, get_all_tasks, get_task, get_files_by_task
from modules.task_queue import process_task_async

app = Flask(__name__)
app.config.from_object(Config)

ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files')
    output_mode = request.form.get('output_mode', 'single')

    if not files:
        return jsonify({'error': 'No files uploaded'}), 400

    task_id = create_task(', '.join([f.filename for f in files]), output_mode)

    upload_dir = os.path.join(Config.UPLOAD_FOLDER, task_id)
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            create_file_record(task_id, filepath)

    process_task_async(task_id)

    return jsonify({'task_id': task_id}), 200

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = get_all_tasks()
    return jsonify(tasks), 200

@app.route('/api/task/<task_id>', methods=['GET'])
def get_task_detail(task_id):
    task = get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    files = get_files_by_task(task_id)
    return jsonify({'task': task, 'files': files}), 200

@app.route('/api/task/<task_id>/download', methods=['GET'])
def download_task(task_id):
    task = get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    output_dir = os.path.join(Config.OUTPUT_FOLDER, task_id)
    if not os.path.exists(output_dir):
        return jsonify({'error': 'Output not found'}), 404

    files = get_files_by_task(task_id)
    mp3_files = [f['mp3_path'] for f in files if f['mp3_path'] and os.path.exists(f['mp3_path'])]

    if not mp3_files:
        return jsonify({'error': 'No MP3 files found'}), 404

    if len(mp3_files) == 1:
        return send_file(mp3_files[0], as_attachment=True)

    # For multiple files, create zip
    import shutil
    zip_path = os.path.join(Config.OUTPUT_FOLDER, f'{task_id}.zip')
    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', output_dir)
    return send_file(zip_path, as_attachment=True)

@app.route('/api/logs', methods=['GET'])
def get_logs():
    log_files = []
    if os.path.exists(Config.LOG_FOLDER):
        for f in os.listdir(Config.LOG_FOLDER):
            if f.startswith('error_'):
                log_files.append({'filename': f})
    return jsonify(log_files), 200

@app.route('/api/logs/<filename>', methods=['GET'])
def get_log_content(filename):
    # Security: only allow error_ prefixed files
    if not filename.startswith('error_') or '..' in filename:
        return jsonify({'error': 'Invalid filename'}), 400

    log_path = os.path.join(Config.LOG_FOLDER, filename)
    if not os.path.exists(log_path):
        return jsonify({'error': 'Log not found'}), 404

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'filename': filename, 'content': content}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/task/<task_id>/retry', methods=['POST'])
def retry_task(task_id):
    task = get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    if task['status'] != 'failed':
        return jsonify({'error': 'Only failed tasks can be retried'}), 400

    process_task_async(task_id)
    return jsonify({'task_id': task_id, 'status': 'pending'}), 200

if __name__ == '__main__':
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
    os.makedirs(Config.LOG_FOLDER, exist_ok=True)
    init_db()
    app.run(debug=True, port=5000)
