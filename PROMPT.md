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

## 批量导入（后台发布接口）

```
# 爬虫数据 → CSV → 后台导入（联动）
cd server/scrapers && python export_and_push.py --push

# 或后台手动上传：管理后台 → 发布实习 → 批量导入 CSV/Excel
# 表头：岗位名称,公司名称,工作城市,岗位类型（必填）+ 其余选填
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
├── search.html         # 搜索
├── login.html          # 登录
├── register.html       # 注册(验证码)
├── profile.html        # 个人主页·分享+收藏
├── edit.html           # 编辑资料·修改密码
├── about.html          # 关于我们·免责·联系
├── terms.html          # 用户协议
├── privacy.html        # 隐私政策
├── admin/index.html    # 管理后台·仪表盘+发布实习+批量导入+反馈管理+一键下架
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
