@echo off
REM 10年期与2年期国债收益率利差分析系统 - HTTP服务器启动脚本 (Windows)

echo ==================================
echo   10Y-2Y 利差分析系统
echo ==================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 Python
    echo 请先安装 Python: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 🚀 启动 HTTP 服务器（端口 8088）...
echo.

cd /d "%~dp0"
start python -m http.server 8088

REM 等待服务器启动
timeout /t 2 /nobreak >nul

echo ✅ 服务器启动成功！
echo.
echo 📊 请在浏览器中访问：
echo    http://localhost:8088/display/10y2y_spread.html
echo.
echo 💡 提示：
echo    - 关闭此命令窗口以停止服务器
echo    - 或按 Ctrl+C 停止服务器
echo.
echo 按任意键打开浏览器...
pause >nul

start http://localhost:8088/display/10y2y_spread.html

echo.
echo 服务器运行中... 按 Ctrl+C 停止
pause
