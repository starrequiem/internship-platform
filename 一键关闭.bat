@echo off
chcp 65001 >nul
title 实习通 · 关闭服务

echo.
echo 正在关闭实习通服务...

:: 关闭 Node.js 后端
taskkill /fi "WINDOWTITLE eq 实习通-后端*" /f >nul 2>&1
:: 关闭 Python 前端
taskkill /fi "WINDOWTITLE eq 实习通-前端*" /f >nul 2>&1
:: 释放端口
for /f "tokens=5" %%a in ('netstat -ano ^| find ":3000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| find ":8080" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo ✅ 已关闭
timeout /t 1 >nul
