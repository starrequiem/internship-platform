@echo off
chcp 65001 >nul 2>&1
title 实习通关闭

echo ========================================
echo   实习通 · 关闭服务
echo ========================================
echo.

echo [1/2] 关闭前后端进程...
:: 按窗口标题杀
taskkill /fi "WINDOWTITLE eq shixitong-backend*" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq shixitong-frontend*" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq 实习通*" /f >nul 2>&1
:: 按端口杀（兜底）
for /f "tokens=5" %%a in ('netstat -ano ^| find ":3000" ^| find "LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| find ":8080" ^| find "LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
echo   [OK] 前后端已关闭
echo.

:: 询问是否停止 MySQL
set /p stopmysql="是否同时停止 MySQL 服务？(y/n): "
if /i "%stopmysql%"=="y" (
    echo   正在停止 MySQL...
    net stop MySQL80 2>nul
    if errorlevel 1 (
        echo   [警告] MySQL 停止失败，可能需要管理员权限
    ) else (
        echo   [OK] MySQL 已停止
    )
) else (
    echo   跳过 MySQL（数据库保持运行）
)

echo.
echo ========================================
echo   已关闭
echo ========================================
pause
