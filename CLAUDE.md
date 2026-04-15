# BookVoice 项目注意事项

## 首次运行

**首次运行 OCR 功能时**，easyocr 会下载模型文件（约 300MB），需要网络连接。

## ffmpeg 安装

如果需要使用合并MP3功能，需要安装 ffmpeg：

```bash
# Windows (使用 Chocolatey)
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt install ffmpeg
```

## Python 3.14 兼容性

pydub 与 Python 3.14 不兼容（audioop 被移除），合并MP3功能在 Python 3.14 上需要延迟导入。

## 启动应用

```bash
cd bookvoice
python app.py
```

然后访问 http://localhost:5000

## 测试

```bash
cd bookvoice
py -m pytest tests/test_config.py tests/test_database.py tests/test_translator.py -v
```

**测试结果：28个测试全部通过**