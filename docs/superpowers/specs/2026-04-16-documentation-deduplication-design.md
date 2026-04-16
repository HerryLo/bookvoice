# Documentation Deduplication Design

**Date:** 2026-04-16
**Topic:** Remove redundant/duplicate content from CLAUDE.md and README.md

## Goal

Each documentation file has a clear, single purpose with no overlapping content. CLAUDE.md is the developer reference; README.md is the user guide.

## File Responsibilities

| File | Purpose | Audience |
|------|---------|----------|
| **CLAUDE.md** | Developer reference: code patterns, API contracts, architecture, config, DB schema | Developers and AI assistant |
| **README.md** | User guide: setup, usage, quick start, troubleshooting | End users |

## Changes to README.md

### Remove (move to CLAUDE.md or delete)
- Detailed project structure tree — replace with a simple 5-line overview
- Database table structure — remove (documented in CLAUDE.md)
- Detailed API endpoint table — remove (incomplete, documented in CLAUDE.md)
- Python/Node.js dependency tables — simplify to just "run install script"
- Testing section — remove (duplicate)

### Keep and simplify
- Brief description (1-2 sentences)
- Prerequisites list (Python, Node.js, ffmpeg)
- Quick start steps (install.bat → py app.py → access localhost:5000)
- Output mode explanation (single vs merged)
- Troubleshooting FAQ (most common issues)

### Structure (target)

```
# BookVoice - 图文转语音系统

1行描述

## 环境要求
- Python, Node.js, ffmpeg

## 快速开始
- install.bat / bash install.sh
- py app.py
- 访问 http://localhost:5000

## 使用说明
- Single 模式
- Merged 模式
- 下载文件

## 常见问题
- TTS语音问题
- 任务一直处理中
- API 401
```

## Changes to CLAUDE.md

### Remove
- Redundant project overview that duplicates README
- Anything not directly needed for code guidance

### Keep
- Code conventions (# comments, no docstrings, route grouping)
- API authentication (X-API-Key)
- API endpoints (complete list)
- Project structure (as reference for developers)
- Database schema (complete with indexes)
- Output mode explanation (technical details)
- Config reference
- Tech stack details

## Self-Review Checklist

- [x] No placeholder/TBD sections
- [x] No internal contradictions
- [x] Scope is focused (documentation only, single implementation)
- [x] Ambiguity resolved: README = user-facing, CLAUDE = developer-facing
