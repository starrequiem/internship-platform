@echo off
chcp 65001 >nul
title 实习通 · 本地服务器
cd /d "%~dp0"
echo.
echo ╔══════════════════════════════════════╗
echo ║   🚀 实习通 · 本地开发服务器          ║
echo ║   地址：http://localhost:8080         ║
echo ║   按 Ctrl+C 停止服务器                ║
echo ║   不要关闭此窗口                      ║
echo ╚══════════════════════════════════════╝
echo.
python server.py
pause
