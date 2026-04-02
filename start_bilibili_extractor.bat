@echo off
chcp 65001 >nul
echo ==========================================
echo  Bilibili 字幕提取工具
echo ==========================================
echo.

cd /d "%~dp0"

python "%~dp0scripts\bilibili_gui_launcher.py"

if errorlevel 1 (
    echo.
    echo 程序运行出错，请检查错误信息
    pause
)
