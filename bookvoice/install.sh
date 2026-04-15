#!/bin/bash
# ========================================
# BookVoice 依赖安装脚本
# ========================================

set -e

cd "$(dirname "$0")"

echo "[1/3] 安装 Python 依赖..."
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo ""
echo "[2/3] 检查 ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "警告: ffmpeg 未安装，MP3合并功能将不可用"
    echo "macOS: brew install ffmpeg"
    echo "Linux: sudo apt install ffmpeg"
else
    echo "ffmpeg 已安装"
fi

echo ""
echo "[3/3] 安装前端依赖..."
cd frontend
npm install

echo ""
echo "========================================"
echo "安装完成！"
echo "========================================"
echo ""
echo "启动方式:"
echo "  py app.py"
echo ""
echo "前端构建（如需）:"
echo "  cd frontend && npm run build"
