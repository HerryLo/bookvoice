# BookVoice - 图文转语音系统

将图片、PDF、Word文档中的文字识别后转换为语音MP3文件。

## 环境要求

| 软件 | 说明 |
|-----|------|
| Python 3.8+ | https://python.org |
| Node.js 16+ | https://nodejs.org |
| ffmpeg | MP3合并功能必需 |

## 快速开始

### 1. 安装依赖

**Windows:** 双击运行 `bookvoice/install.bat`
**macOS/Linux:** `bash bookvoice/install.sh`

### 2. 启动应用

```bash
cd bookvoice
python app.py
```

### 3. 访问

打开浏览器访问 http://localhost:5000

> 首次运行 OCR 功能时，easyocr 会下载模型文件（约 300MB）。

## 使用说明

### 上传文件

点击上传按钮，选择图片（PNG、JPG）、PDF 或 Word 文档。

### 输出模式

- **Single 模式**：每个文档独立生成一个 MP3，多文档打包 ZIP 下载
- **Merged 模式**：所有文档合并成一个 MP3 下载

### 下载

任务完成后，点击"下载"按钮获取 MP3 文件。

## 常见问题

### 任务一直显示"处理中"
- 任务在后台异步处理
- 任务列表会自动刷新（每3秒）
- 稍等片刻即可

### TTS语音问题
- 仅支持 Windows 系统
- 需要安装 ffmpeg：`choco install ffmpeg`

### API 返回 401 Unauthorized
- 前端已配置默认 API Key：`dev-key-change-me`
- 可通过环境变量 `BOOKVOICE_API_KEY` 修改