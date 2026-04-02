@echo off
chcp 65001 >nul
echo ================================================
echo    BiliGlass Web 启动器
echo ================================================
echo.
echo 启动前端和后端...
cd /d "%~dp0"
python scripts\start_biliglass_web.py
if errorlevel 1 (
    echo.
    echo Web 启动失败，请查看上方错误信息。
)
pause