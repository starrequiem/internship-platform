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
python scrape_bytedance.py          # 字节（反爬强，仅首屏）
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

### 1. 文本爬取分割有待优化
- 牛客/字节的整页文本分割仍不准：title/company 偶有错位、requirements 提取不全
- 待优化 `extract.py`（split_detail 边界识别）、`segment_company.py`（字节整页分割）
- 可引入 AI 分割兜底（`ai_parse.py` + `AI_PARSE_PROMPT.md` 已具备框架）

### 2. 封装上线公网
- 当前仅本地开发（localhost:8080 / 3000）
- 待做：环境变量管理（DB 密码、JWT 密钥移出代码）、HTTPS、域名、进程守护（pm2）

### 3. 云服务器搭建
- 选型 + 部署：云服务器（MySQL 8.0 / Node / Python / Playwright 依赖）
- Nginx 反向代理前后端、定时爬虫任务、数据库备份
