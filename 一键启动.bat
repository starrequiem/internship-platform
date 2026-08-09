@echo off
chcp 65001 >nul 2>&1
title 实习通启动

echo ========================================
echo   实习通 · 一键启动
echo ========================================
echo.

echo [1/3] MySQL...
sc query MySQL80 | find "RUNNING" >nul 2>&1
if errorlevel 1 (
    echo   尝试启动 MySQL（如失败请以管理员运行或手动启动）...
    net start MySQL80 2>nul
    if errorlevel 1 echo   [警告] MySQL 启动失败，请手动启动
)
echo.

echo [2/3] 后端 API (3000)...
start "shixitong-backend" cmd /k "cd /d %~dp0server && node app.js"
ping -n 4 127.0.0.1 >nul
echo.

echo [3/3] 前端页面 (8080)...
start "shixitong-frontend" cmd /k "cd /d %~dp0 && python server.py"
ping -n 4 127.0.0.1 >nul
echo.

echo ========================================
echo   全部启动完成
echo   http://localhost:8080
echo ========================================
start http://localhost:8080
