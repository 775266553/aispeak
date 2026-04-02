@echo off
chcp 65001 >nul
echo ================================================
echo    Bilibili 字幕提取工具 v2.0
echo ================================================
echo.
echo 启动GUI界面...
cd /d "%~dp0"
python scripts\bilibili_gui_launcher.py
pause
