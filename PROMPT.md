# 实习通 · 全栈开发提示词

> 任何 AI 可直接调用以下命令来维护和开发本网站

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

## 抓取数据

```
cd server/scrapers && python scraper.py
```

## 网站维护

```
# 查看状态
node maintenance/cleanup.js --stats

# 一键下架已截止实习
node maintenance/cleanup.js --do
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
后端: Node.js + Express (端口3000)
数据库: MySQL 8.0
爬虫: Python + Playwright + Scrapling
```

## 项目结构

```
├── index.html          # 首页·实习列表+筛选+翻页
├── detail.html         # 实习详情·联系信息+收藏+举报
├── publish.html        # 发布实习
├── search.html         # 搜索
├── login.html          # 登录
├── register.html       # 注册(验证码)
├── profile.html        # 个人主页·分享+收藏
├── edit.html           # 编辑资料·修改密码
├── admin/index.html    # 管理后台·仪表盘+一键下架
├── js/                 # api.js auth.js components.js
├── css/style.css       # 全局样式
├── server/             # Express后端
│   ├── app.js          # 入口
│   ├── db.js           # MySQL连接
│   └── routes/         # API路由
├── server/scrapers/    # Python爬虫
├── maintenance/        # 维护脚本
└── sql/                # 数据库脚本
```
