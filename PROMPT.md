# 实习通 · 全栈开发提示词

> 任何 AI 可直接调用以下命令来维护和开发本网站

## 项目定位

**单向分享实习信息平台**：仅管理员发布岗位，用户浏览 / 搜索 / 收藏 / 举报。
数据来源：爬虫抓取（牛客汇总站 + 6 家大厂官网 API）。

## 启动服务

```
# 1. 启动MySQL
net start MySQL80

# 2. 启动后端API (端口3000)
cd server && node app.js

# 3. 启动前端 (端口8080)
cd .. && python server.py

# 访问: http://localhost:8080
# 管理后台: http://localhost:8080/admin/index.html
# 管理员: admin / admin123
```

快捷方式：双击「一键启动.bat」启动全部 → 「一键进入后台.bat」直达后台。

## 维护入口（菜单式）

双击 `维护/一键维护.bat`，终端菜单可选：
1. 爬虫抓取数据（再选站点配置）
2. 一键下架过期信息
3. 岗位去重
4. 查看数据库状态

## 抓取数据（多站点，在 server/scrapers/ 下）

```
python scraper.py --site nowcoder   # 牛客汇总（列表页+详情）
python scrape_meituan.py            # 美团（API，实习/校招）
python scrape_alibaba.py            # 阿里（API，需 XSRF-TOKEN）
python scrape_xiaohongshu.py        # 小红书（API，SPA 宿主免鉴权）
python scrape_tencent.py            # 腾讯（API，分页）
python scrape_huawei.py             # 华为（API，需 session+Referer）
python scrape_bytedance.py          # 字节（API + CSRF token）
python scrape_netease.py            # 网易（API，campus.163.com + 游戏）
python scrape_shixiseng.py          # 实习僧（列表+详情 SSR）
python export_and_push.py --push    # 导出 CSV 并推送后台导入接口
```

各站 API 逆向方案参考：github.com/HA7CH/job-pro（meituan.ts / alibaba.ts / huawei.ts / xiaohongshu.ts / tencent.ts / bytedance.ts）。

## 批量导入（后台发布接口）

```
# 爬虫数据 → CSV → 后台导入（联动）
cd server/scrapers && python export_and_push.py --push

# 或后台手动上传：管理后台 → 发布实习 → 批量导入 CSV/Excel
# 表头：岗位名称,公司名称,工作城市,岗位类型（必填）+ 其余选填
```

## 网站维护

```
node maintenance/cleanup.js --stats   # 查看状态
node maintenance/cleanup.js --do      # 一键下架已截止实习
node maintenance/dedup.js --do        # 岗位去重（同 title+company+city）
```

## 数据库

```
MySQL: localhost:3306 / internship_platform / root / 200619
表: users, internships, favorites, tags, internship_tags, thanks, reports
迁移: sql/migration-v2.sql
```

## 技术栈

```
前端: HTML/CSS/JS (H5响应式)
后端: Node.js + Express (端口3000) + multer + xlsx
数据库: MySQL 8.0
爬虫: Python + Playwright + requests + xlsx
```

## 项目结构

```
├── index.html / detail.html / search.html / login.html / register.html
├── profile.html / edit.html / about.html / terms.html / privacy.html
├── admin/index.html    # 管理后台·仪表盘+发布+批量导入+反馈管理+下架
├── js/ css/ components/
├── server/             # Express后端 (app.js + db.js + routes/)
├── server/scrapers/    # 爬虫主脚本 + sites/ 配置模块 + extract.py
├── maintenance/        # 维护脚本 (cleanup / fetch / dedup)
├── 维护/               # 一键维护.bat + 处理过期信息/ + 爬虫/副本
├── sql/                # 建表/迁移脚本
└── 一键启动.bat / 一键关闭.bat / 一键进入后台.bat
```

## 下次工作开展

### 1. ✅ 文本爬取分割优化（已完成 2026-08-17）
- `extract.py`：页尾噪音截断、无标题描述边界识别、修复「职位详情页」误判、投递时间提取
- `segment_company.py`：字节整页描述只取职责列表、去页尾导航/页码
- `config.py`：公司名兜底支持括号/英文、去除·HR后缀
- 新增 `apply_time`（投递时间）字段贯通 DB/爬虫/API/前端，无投递时间显示「详见原页面」
- 牛客列表分页翻页、字节 API 增加 CSRF token 适配

### 2. 封装上线公网
- 当前仅本地开发（localhost:8080 / 3000）
- 待做：环境变量管理（DB 密码、JWT 密钥移出代码）、HTTPS、域名、进程守护（pm2）
- 前端 `python server.py` 单线程，上线前建议换 nginx / http-server

### 3. 云服务器搭建
- 选型 + 部署：云服务器（MySQL 8.0 / Node / Python / Playwright 依赖）
- Nginx 反向代理前后端、定时爬虫任务、数据库备份

### 4. 已知数据/爬取问题
- 牛客「去官网投」类岗位真实雇主未知（company 标记为「待识别」）
- 华为校招淡季岗位极少（季节开放后重跑即可）
- AI 分割兜底框架已具备（`ai_parse.py`），尚未接入实际爬取流程
