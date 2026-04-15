from functools import wraps
from flask import Flask, render_template, request, jsonify, send_file
import os
import uuid
import logging
from werkzeug.utils import secure_filename
from config import Config
from modules.database import init_db, create_task, create_file_record, get_all_tasks, get_task, get_files_by_task, delete_task, delete_file
from modules.task_queue import process_task_async

app = Flask(__name__)
app.config.from_object(Config)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
app.logger.setLevel(logging.INFO)

# ---------------------------------------------------------
# 前端静态文件服务配置
# 前端源码在 frontend/ 目录，构建后输出到 static/ 目录
# Flask 同时提供 API 和前端页面服务
# ---------------------------------------------------------
app.static_folder = 'static'           # 静态文件根目录
app.static_url_path = '/assets'       # 静态文件 URL 前缀

ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS
ALLOWED_OUTPUT_MODES = {'single', 'merged'}
API_KEY = os.environ.get('BOOKVOICE_API_KEY', 'dev-key-change-me')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def verify_api_key(f):
    # API 认证装饰器 - 所有 /api/ 开头的路由需要 X-API-Key header
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ---------------------------------------------------------
# 前端页面路由
# ---------------------------------------------------------
@app.route('/')
def index():
    # GET / - 返回前端 Vue SPA 入口页面
    return send_file(os.path.join(Config.BASE_DIR, 'static', 'index.html'))

@app.route('/assets/<path:filename>')
def serve_static(filename):
    # GET /assets/<filename> - 服务前端构建后的静态资源（JS/CSS/图片等）
    # 实际文件在 static/assets/ 目录下
    return send_file(os.path.join(Config.BASE_DIR, 'static', 'assets', filename))

# ---------------------------------------------------------
# API 路由（需要 X-API-Key 认证）
# ---------------------------------------------------------

# ---------- 任务相关 ----------

@app.route('/api/tasks', methods=['GET'])
@verify_api_key
def get_tasks():
    # GET /api/tasks - 获取所有任务列表
    tasks = get_all_tasks()
    return jsonify(tasks), 200

@app.route('/api/task/<task_id>', methods=['GET'])
@verify_api_key
def get_task_detail(task_id):
    # GET /api/task/<task_id> - 获取指定任务的详细信息（含关联文件列表）
    task = get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    files = get_files_by_task(task_id)
    return jsonify({'task': task, 'files': files}), 200

@app.route('/api/task/<task_id>/retry', methods=['POST'])
@verify_api_key
def retry_task(task_id):
    # POST /api/task/<task_id>/retry - 重新执行失败的任务
    task = get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    if task['status'] != 'failed':
        return jsonify({'error': 'Only failed tasks can be retried'}), 400
    process_task_async(task_id)
    return jsonify({'task_id': task_id, 'status': 'pending'}), 200

@app.route('/api/task/<task_id>/download', methods=['GET'])
@verify_api_key
def download_task(task_id):
    # GET /api/task/<task_id>/download - 下载任务生成的MP3文件（单文件直接返回， 多文件打包ZIP返回）
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
    # 多文件打包为 ZIP
    import shutil
    zip_path = os.path.join(Config.OUTPUT_FOLDER, f'{task_id}.zip')
    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', output_dir)
    return send_file(zip_path, as_attachment=True)

@app.route('/api/task/<task_id>', methods=['DELETE'])
@verify_api_key
def delete_task_api(task_id):
    # DELETE /api/task/<task_id> - 删除整个任务（同时删除上传文件和生成的MP3，只能删除 completed/failed 状态的任务）
    task = get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    if task['status'] not in ('completed', 'failed'):
        return jsonify({'error': 'Cannot delete task in processing'}), 400
    delete_task(task_id)
    return jsonify({'message': 'Task deleted'}), 200

# ---------- 文件相关 ----------

@app.route('/api/file/<int:file_id>', methods=['DELETE'])
@verify_api_key
def delete_file_api(file_id):
    # DELETE /api/file/<file_id> - 删除单个文件（同时删除原文件和MP3，删除后任务无文件时自动删除任务，只能删除 completed/failed 任务的文件）
    from modules.database import get_file
    file_record = get_file(file_id)
    if not file_record:
        return jsonify({'error': 'File not found'}), 404
    task = get_task(file_record['task_id'])
    if not task or task['status'] not in ('completed', 'failed'):
        return jsonify({'error': 'Cannot delete file from task in processing'}), 400
    delete_file(file_id)
    return jsonify({'message': 'File deleted'}), 200

# ---------- 上传相关 ----------

@app.route('/api/upload', methods=['POST'])
@verify_api_key
def upload():
    # POST /api/upload - 上传文件创建新任务（支持多文件，output_mode: single=独立MP3, merged=合并MP3）
    files = request.files.getlist('files')
    output_mode = request.form.get('output_mode', 'single')
    if output_mode not in ALLOWED_OUTPUT_MODES:
        return jsonify({'error': 'Invalid output_mode'}), 400
    if not files:
        return jsonify({'error': 'No files uploaded'}), 400
    task_id = create_task(', '.join([f.filename for f in files]), output_mode)
    upload_dir = os.path.join(Config.UPLOAD_FOLDER, task_id)
    os.makedirs(upload_dir, exist_ok=True)
    for file in files:
        if file and allowed_file(file.filename):
            # 分离原始文件名和扩展名，用 secure_filename 处理文件名部分
            original_filename = file.filename
            parts = original_filename.rsplit('.', 1)
            if len(parts) == 2 and parts[1].lower() in ALLOWED_EXTENSIONS:
                # 有扩展名且扩展名合法
                name_part = secure_filename(parts[0]) or 'file'
                ext_part = parts[1].lower()
                filename = f"{name_part}.{ext_part}"
            else:
                # 无扩展名或扩展名不合法，使用原文件名
                filename = secure_filename(original_filename)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            create_file_record(task_id, filepath)
    process_task_async(task_id)
    return jsonify({'task_id': task_id}), 200

# ---------- 日志相关 ----------

@app.route('/api/logs', methods=['GET'])
@verify_api_key
def get_logs():
    # GET /api/logs - 获取所有错误日志文件列表
    log_files = []
    if os.path.exists(Config.LOG_FOLDER):
        for f in os.listdir(Config.LOG_FOLDER):
            if f.startswith('error_'):
                log_files.append({'filename': f})
    return jsonify(log_files), 200

@app.route('/api/logs/<filename>', methods=['GET'])
@verify_api_key
def get_log_content(filename):
    # GET /api/logs/<filename> - 获取指定错误日志文件内容（仅限 error_ 前缀的文件）
    # 安全检查：只允许读取 error_ 前缀的文件，防止路径遍历
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
        app.logger.error(f"Failed to read log file {filename}: {e}")
        return jsonify({'error': 'Failed to read log file'}), 500

# ---------------------------------------------------------
# 启动应用
# ---------------------------------------------------------
if __name__ == '__main__':
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
    os.makedirs(Config.LOG_FOLDER, exist_ok=True)
    init_db()
    app.run(debug=False, port=5000)
