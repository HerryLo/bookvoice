# MP3 输出模式设计

## 背景

用户需要两种 MP3 输出模式：
- **Single 模式**：每个文档生成一个 MP3（长文档内部合并），多文档下载打包 ZIP
- **Merged 模式**：所有文档合并成一个 MP3，统一下载

## 术语定义

| 术语 | 说明 |
|------|------|
| 分片 | 将超长文本拆分成的小段落（用于 TTS 处理） |
| 文档内合并 | Single 模式下，同一文档内的分片 MP3 合并成一个 MP3 |
| 文档间合并 | Merged 模式下，所有文档的 MP3 合并成一个大 MP3 |

## 设计方案

### Single 模式

1. 文档 OCR/翻译后，按 `\n\n` 分割成段落
2. 调用 `text_to_speech_segments_with_progress()` 逐个 TTS 生成段落 MP3
3. 分片 MP3 通过 `merge_mp3_files()` 合并成该文档的单一 MP3
4. 每个文档最终产出一个 MP3
5. 下载时：如果有多个 MP3，打包成 ZIP

### Merged 模式

1. 每个文档分别按 Single 模式处理（分片 → TTS → 文档内合并）
2. 收集所有文档的 MP3 路径
3. 调用 `merge_mp3_files()` 将所有 MP3 合并成一个大 MP3
4. 下载时：直接返回这一个合并后的 MP3

## 数据流

```
Single 模式：
  文档 → OCR → 翻译 → 按段落分割 → TTS逐段生成MP3 → 文档内合并 → 该文档单一MP3
         ↓
  多文档 → 各自生成MP3 → ZIP打包下载

Merged 模式：
  文档1 → ... → MP3_1
  文档2 → ... → MP3_2
  文档3 → ... → MP3_3
         ↓
  所有MP3 → 文档间合并 → 单一MP3 → 下载
```

## 修改文件

### `modules/task_queue.py`

修改 `process_task()` 方法：

```python
def process_task(self, task_id: str):
    task = get_task(task_id)
    if not task:
        return

    update_task_status(task_id, 'processing')
    files = get_files_by_task(task_id)
    output_mode = task.get('output_mode', 'single')

    output_dir = os.path.join(Config.OUTPUT_FOLDER, task_id)
    os.makedirs(output_dir, exist_ok=True)

    all_mp3_paths = []

    for file_record in files:
        try:
            # OCR / 翻译...
            text = ...
            translated_text = self.processors['translator'].translate_to_chinese(text)

            # 按段落分割
            paragraphs = [p.strip() for p in translated_text.split('\n\n') if p.strip()]
            update_file_segments(file_record['id'], len(paragraphs))

            def update_progress(processed_count):
                update_file_progress(file_record['id'], processed_count)

            # TTS 生成
            mp3_paths = self.processors['tts'].text_to_speech_segments_with_progress(
                paragraphs, output_dir, progress_callback=update_progress
            )

            # 文档内合并
            if mp3_paths:
                doc_mp3 = os.path.join(output_dir, f'{file_record["id"]}.mp3')
                merge_mp3_files(mp3_paths, doc_mp3)
                all_mp3_paths.append(doc_mp3)
                update_file_status(file_record['id'], 'completed', doc_mp3)

            update_file_progress(file_record['id'], len(paragraphs))

        except Exception as e:
            update_file_status(file_record['id'], 'failed')
            self._log_error(task_id, file_record['original_path'], str(e))

    # 文档间合并（merged 模式）
    if output_mode == 'merged' and len(all_mp3_paths) > 1:
        merged_path = os.path.join(output_dir, 'merged.mp3')
        from .mp3_merger import merge_mp3_files
        merge_mp3_files(all_mp3_paths, merged_path)
        # 更新第一个文件的 mp3_path 为合并后的路径
        if files:
            update_file_status(files[0]['id'], 'completed', merged_path)

    # 更新任务状态
    files = get_files_by_task(task_id)
    any_success = any(f['status'] == 'completed' for f in files)
    update_task_status(task_id, 'completed' if any_success else 'failed')
```

### `app.py`

修改 `/api/task/<task_id>/download` 路由：

```python
@app.route('/api/task/<task_id>/download', methods=['GET'])
@verify_api_key
def download_task(task_id):
    task = get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    output_dir = os.path.join(Config.OUTPUT_FOLDER, task_id)
    if not os.path.exists(output_dir):
        return jsonify({'error': 'Output not found'}), 404

    output_mode = task.get('output_mode', 'single')

    # merged 模式：直接返回合并后的 MP3
    if output_mode == 'merged':
        merged_path = os.path.join(output_dir, 'merged.mp3')
        if os.path.exists(merged_path):
            return send_file(merged_path, as_attachment=True)
        return jsonify({'error': 'Merged MP3 not found'}), 404

    # single 模式：多文件打包 ZIP
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

## 边界情况

| 情况 | 处理方式 |
|------|----------|
| 单文档 single 模式 | 直接返回该文档的 MP3 |
| 多文档 single 模式 | ZIP 打包 |
| 单文档 merged 模式 | 文档内合并后返回单一 MP3 |
| merged 但合并失败 | 返回第一个文档的 MP3 或 404 |
| 分片生成失败 | 跳过该分片，记录日志，继续处理 |

## 测试要点

1. Single 模式上传单文档 → 下载得到 1 个 MP3
2. Single 模式上传多文档 → 下载得到 ZIP（内含 N 个 MP3）
3. Merged 模式上传多文档 → 下载得到 1 个合并后的 MP3
4. 长文档分片后合并音质连贯
