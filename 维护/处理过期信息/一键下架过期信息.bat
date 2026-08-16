@echo off
chcp 936 >nul 2>&1
title 实习通 - 一键下架过期信息

echo ========================================
echo   实习通 - 一键下架已截止实习
echo ========================================
echo.

cd /d "C:\Users\屠庭宇\Desktop\internship-platform"

echo   正在关闭所有已截止的实习信息...
echo.
node maintenance\cleanup.js --do
echo.
echo ========================================
echo   完成！按任意键关闭窗口。
echo ========================================
pause
