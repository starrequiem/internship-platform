@echo off
chcp 65001 >nul
title 实习通 · 一键启动

echo.
echo ══════════════════════════════════════
echo   实习通 · 正在启动...
echo ══════════════════════════════════════
echo.

:: 1. 确保 MySQL 正在运行
echo [1/3] 检查 MySQL 服务...
sc query MySQL80 | find "RUNNING" >nul
if %errorlevel% neq 0 (
    echo   启动 MySQL...
    net start MySQL80 >nul 2>&1
)
echo   ✅ MySQL 已就绪

:: 2. 启动后端 (Node.js)
echo [2/3] 启动后端 API (端口 3000)...
start "实习通-后端" cmd /k "cd /d %~dp0server && echo 🚀 实习通 API 启动中... && node app.js"

:: 等后端先起来
timeout /t 2 /nobreak >nul

:: 3. 启动前端 (Python)
echo [3/3] 启动前端页面 (端口 8080)...
start "实习通-前端" cmd /k "cd /d %~dp0实习通-静态演示版 && echo 📄 实习通前端启动中... && python server.py"

:: 等前端起来
timeout /t 1 /nobreak >nul

:: 4. 打开浏览器
echo.
echo ══════════════════════════════════════
echo   ✅ 全部启动完成！
echo   浏览器即将打开 http://localhost:8080
echo.
echo   关闭方式：分别关闭两个弹窗
echo   （后端窗口 和 前端窗口 各按 Ctrl+C）
echo ══════════════════════════════════════
start http://localhost:8080

pause
