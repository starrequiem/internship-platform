@echo off
chcp 936 >nul 2>&1
title 实习通 - 一键维护

:menu
cls
echo ============================================
echo   实习通 - 一键维护
echo ============================================
echo.
echo   [1] 爬虫抓取数据
echo   [2] 一键下架过期信息
echo   [3] 岗位去重
echo   [4] 查看数据库状态
echo   [0] 退出
echo.
set /p choice=请选择操作 (0-4): 

if "%choice%"=="1" goto scraper
if "%choice%"=="2" goto cleanup
if "%choice%"=="3" goto dedup
if "%choice%"=="4" goto stats
if "%choice%"=="0" exit
goto menu

:scraper
cls
echo ============================================
echo   爬虫抓取 - 选择站点配置
echo ============================================
echo.
echo   [1] 牛客网 (汇总站)
echo   [2] 字节跳动
echo   [3] 腾讯
echo   [4] 美团
echo   [5] 阿里巴巴
echo   [6] 华为
echo   [7] 小红书
echo   [8] 全部大厂 (耗时较长)
echo   [0] 返回上级
echo.
set /p sc=请选择站点 (0-8): 

cd /d "C:\Users\屠庭宇\Desktop\internship-platform\server\scrapers"

if "%sc%"=="1" python scraper.py --site nowcoder
if "%sc%"=="2" python scrape_bytedance.py
if "%sc%"=="3" python scrape_tencent.py
if "%sc%"=="4" python scrape_meituan.py
if "%sc%"=="5" python scrape_alibaba.py
if "%sc%"=="6" python scrape_huawei.py
if "%sc%"=="7" python scrape_xiaohongshu.py
if "%sc%"=="8" goto runall
if "%sc%"=="0" goto menu
echo.
echo 抓取完成，按任意键返回菜单...
pause >nul
goto menu

:runall
python scrape_meituan.py
python scrape_alibaba.py
python scrape_huawei.py
python scrape_xiaohongshu.py
python scrape_tencent.py
echo.
echo 全部大厂抓取完成，按任意键返回菜单...
pause >nul
goto menu

:cleanup
cd /d "C:\Users\屠庭宇\Desktop\internship-platform"
node maintenance\cleanup.js --do
echo.
pause
goto menu

:dedup
cd /d "C:\Users\屠庭宇\Desktop\internship-platform"
node maintenance\dedup.js --do
echo.
pause
goto menu

:stats
cd /d "C:\Users\屠庭宇\Desktop\internship-platform"
node maintenance\cleanup.js --stats
echo.
pause
goto menu
