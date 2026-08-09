# 实习通 · 网站维护 AI 提示词

> 任何 AI（Claude、GPT、Gemini 等）均可直接使用以下提示词来维护本网站。
> 确保 AI 的工作目录为项目根目录。

---

## 1. 一键下架已截止实习

```
用 Node.js 运行 maintenance/cleanup.js --do，关闭所有已截止的实习信息
```

预览模式（不执行，只查看）：
```
运行 maintenance/cleanup.js，列出已截止但未下架的实习
```

查看网站统计：
```
运行 maintenance/cleanup.js --stats，显示当前网站状态
```

---

## 2. 抓取最新实习数据

```
运行 maintenance/fetch.js，完整流程：抓取→解析→入库
```

分步执行：
```
运行 maintenance/fetch.js --scrape   # 只抓取
运行 maintenance/fetch.js --parse    # 只解析
运行 maintenance/fetch.js --insert   # 只入库
```

---

## 3. 启动/重启网站

```
先确保 MySQL 服务已启动，然后：
cd server && node app.js          # 启动后端 API (端口3000)
cd .. && python server.py         # 启动前端 (端口8080)
```

需要先杀掉旧进程：
```
taskkill //F //IM node.exe
```

---

## 4. 数据库维护

```
连接 MySQL 数据库 internship_platform，执行维护操作：
- 查看重复岗位：SELECT title, company, city, COUNT(*) FROM internships GROUP BY title, company, city HAVING COUNT(*) > 1;
- 清理7天前的已关闭岗位：DELETE FROM internships WHERE status='closed' AND updated_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
```

---

## 5. 快速健康检查

```
检查以下服务是否正常运行：
1. MySQL 数据库 internship_platform
2. 后端 API: curl http://localhost:3000/api/health
3. 前端页面: curl -o /dev/null -w "%{http_code}" http://localhost:8080/index.html
4. 实习总数: curl -s http://localhost:3000/api/internships | python -c "import sys,json; print(json.load(sys.stdin)['total'])"
```

---

## 6. 项目技术栈说明

```
- 前端: 纯 HTML/CSS/JS，H5响应式，localhost:8080
- 后端: Node.js + Express，localhost:3000
- 数据库: MySQL 8.0，数据库名 internship_platform
- 爬虫: Python + Scrapling + Playwright，server/scrapers/
- 维护脚本: Node.js，maintenance/

数据库表结构：sql/schema-mysql.sql
后端路由：server/routes/*.js
前端页面：根目录 *.html
```

---

## 7. 常见问题处理

```
问题：页面无法访问
→ 检查后端 node app.js 是否在运行
→ 检查前端 python server.py 是否在运行
→ 检查 MySQL 服务是否启动

问题：爬虫获取不到数据
→ 检查 Playwright 浏览器是否安装: python -c "from playwright.sync_api import sync_playwright; print('OK')"
→ 手动运行: cd server/scrapers && python main.py test

问题：注册验证码在哪看
→ 查看 node app.js 的控制台输出，验证码会打印在那里

问题：密码改不了
→ 每个账号7天内只能改一次密码
→ 管理员可手动重置: UPDATE users SET password_changed_at = NULL WHERE username = '用户名';
```
