# BookVoice - 图文转语音系统设计

**日期**: 2026-04-14
**状态**: 已批准

---

## 1. 项目概述

### 1.1 目标
为懒人/听书用户构建一个Web管理系统，支持从图片、PDF、Word文档中提取文字，翻译英文内容，并通过本地TTS生成MP3音频文件。

### 1.2 用户场景
- 个人用户：喜欢听书而非阅读
- 输入源：手机照片、截图、PDF、Word文档
- 输出：分章节分段的MP3文件

---

## 2. 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| Web框架 | Flask | 轻量易维护 |
| OCR | EasyOCR | 支持中英文，离线 |
| PDF处理 | pdfplumber | 文字/表格提取 |
| Word处理 | python-docx | 文字提取 |
| 翻译 | googletrans | 英文→中文，需联网 |
| TTS | pyttsx3 | Windows本地TTS，离线 |
| 前端 | Vue3 + Element Plus | 现代化管理界面 |

---

## 3. 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   Web 管理界面                        │
│  (上传 / 任务列表 / 下载 / 日志)                       │
└─────────────────┬───────────────────────────────────┘
                  │ HTTP
┌─────────────────▼───────────────────────────────────┐
│              Flask 后端服务                           │
│  (任务队列 / 进度跟踪 / 文件管理)                      │
└─────────────────┬───────────────────────────────────┘
                  │ 线程/进程
┌─────────────────▼───────────────────────────────────┐
│              处理模块 (后台线程)                       │
│  文本提取 → 翻译 → TTS → MP3                          │
└─────────────────────────────────────────────────────┘
```

---

## 4. 目录结构

```
bookvoice/
├── app.py                  # Flask主应用
├── config.py               # 配置文件
├── requirements.txt        # 依赖列表
├── static/                 # 静态文件(CSS/JS)
├── templates/              # HTML模板(Vue挂载点)
│   └── index.html          # Vue单页应用入口
├── src/                     # Vue源码
│   ├── main.js             # Vue入口
│   ├── App.vue             # 根组件
│   ├── api/                # API调用
│   ├── views/              # 页面组件
│   │   ├── TaskList.vue    # 任务列表
│   │   ├── Upload.vue      # 文件上传
│   │   └── Logs.vue        # 日志查看
│   └── components/         # 通用组件
├── uploads/                # 上传文件目录
│   └── [任务ID]/
├── outputs/                # 生成的MP3文件
│   └── [任务ID]/
├── logs/                   # 错误日志
│   └── error_<timestamp>.log
└── modules/
    ├── __init__.py
    ├── ocr.py              # OCR识别
    ├── translator.py        # 翻译模块
    ├── tts.py              # TTS转换
    ├── pdf_handler.py       # PDF处理
    ├── word_handler.py      # Word处理
    └── task_queue.py        # 任务队列
```

---

## 5. 功能模块

### 5.1 文件上传
- 支持格式：PNG, JPG, JPEG, PDF, DOCX
- 支持单文件或批量上传
- 上传后创建任务记录

### 5.2 任务管理
- 状态流转：待处理 → 处理中 → 完成 / 失败
- 显示处理进度百分比
- 支持重试失败任务

### 5.3 文本提取流程
```
图片 → EasyOCR → 结构化文本（段落/标题）
PDF  → pdfplumber → 结构化文本
Word → python-docx → 结构化文本
```

### 5.4 翻译流程
- 检测文本语言
- 若为英文，翻译为中文
- 若为中文，直接使用

### 5.5 TTS转换
- 使用Windows pyttsx3
- 按段落分句生成音频
- 输出MP3格式

### 5.6 MP3下载
- 单个MP3下载
- 批量打包下载（ZIP）

---

## 6. 输出模式

| 模式 | 说明 |
|------|------|
| 独立MP3 | 每个输入文件 → 独立MP3 |
| 合并MP3 | 批量处理 → 单个MP3 |

---

## 7. 错误处理

### 7.1 策略
- `skip_on_error = True`：跳过失败文件，记录日志，继续处理
- `skip_on_error = False`：中断处理，提示用户

### 7.2 日志记录
- 路径：`logs/error_<timestamp>.log`
- 内容：文件名、错误原因、时间戳
- Web界面查看

---

## 8. 数据库设计（SQLite）

### 8.1 tasks 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PRIMARY KEY | UUID |
| filename | TEXT | 原始文件名 |
| status | TEXT | pending/processing/completed/failed |
| error_msg | TEXT | 错误信息（可选） |
| created_at | DATETIME | 创建时间 |
| completed_at | DATETIME | 完成时间（可选） |
| output_mode | TEXT | single/merged |

### 8.2 files 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增ID |
| task_id | TEXT | 关联任务ID |
| original_path | TEXT | 原始文件路径 |
| mp3_path | TEXT | 输出MP3路径（可选） |
| status | TEXT | pending/processed/failed |

---

## 9. API 设计

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 任务列表页面 |
| `/upload` | GET/POST | 文件上传 |
| `/tasks` | GET | 获取任务列表（JSON） |
| `/task/<id>` | GET | 获取任务详情 |
| `/task/<id>/retry` | POST | 重试失败任务 |
| `/task/<id>/download` | GET | 下载MP3 |
| `/logs` | GET | 日志页面 |
| `/logs/api` | GET | 获取日志（JSON） |

---

## 10. 页面设计（Vue + Element UI组件）

### 10.1 TaskList.vue - 任务列表
- Element UI Table 展示任务列表
- 状态标签（el-tag）
- 进度条（el-progress）
- 下载/重试按钮（el-button）

### 10.2 Upload.vue - 文件上传
- el-upload 拖拽上传组件
- 文件类型说明
- 输出模式选择（el-radio-group）
- 上传进度（el-progress）

### 10.3 Logs.vue - 日志查看
- el-table 展示错误日志
- 时间筛选（el-date-picker）
- 详情弹窗（el-dialog）

---

## 11. 配置项

```python
# config.py
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
LOG_FOLDER = 'logs'
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
SKIP_ON_ERROR = True  # 可配置
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'docx'}
```

---

## 12. 依赖

**后端 (Python)**
```
Flask>=2.0
easyocr>=1.4
pdfplumber>=0.5
python-docx>=0.8
googletrans>=3.0.0
pyttsx3>=2.90
Werkzeug>=2.0
```

**前端 (Node.js)**
```
vue@3.x
element-plus
axios
vite@4.x
```

---

## 13. 待确认事项

- [ ] Windows TTS语音包选择（可配置）
- [ ] 翻译API备用方案（googletrans不稳定时）
