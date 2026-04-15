@echo off
chcp 65001 >nul
echo ========================================
echo BookVoice 依赖安装脚本
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 安装 Python 依赖...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo Python 依赖安装失败！
    pause
    exit /b 1
)
echo.

echo [2/3] 检查 ffmpeg...
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo 警告: ffmpeg 未安装，MP3合并功能将不可用
    echo 请运行: choco install ffmpeg
    echo.
)
echo.

echo [3/3] 安装前端依赖...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo 前端依赖安装失败！
    pause
    exit /b 1
)
cd ..
echo.

echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 启动方式:
echo   py app.py
echo.
echo 前端构建（如需）:
echo   cd frontend ^&^& npm run build
echo.
pause
