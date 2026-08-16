@echo off
chcp 936 >nul 2>&1
title 实习通 - 管理后台入口

echo ========================================
echo   实习通 - 进入管理后台
echo ========================================
echo.

echo   正在打开管理后台...
echo   地址: http://localhost:8080/admin/index.html
echo   账号: admin / admin123
echo.

start http://localhost:8080/admin/index.html

echo   已打开浏览器。
echo   若页面打不开，请先运行「一键启动.bat」。
echo.
pause
