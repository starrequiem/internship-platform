# 爬虫提示词

> 任何 AI 可直接调用以下命令来抓取实习数据

## 全量抓取

```
运行 server/scrapers/scraper.py，从牛客网6个城市列表页收集链接，
逐条访问详情页提取完整职位描述、任职要求、技术标签，
自动入库到 MySQL internship_platform。
```

## 分步执行

```
cd server/scrapers

# 1. 只抓取列表页文本
python targeted_scraper.py

# 2. 只解析已抓取的文本
python nowcoder_parser.py

# 3. 只入库已解析的数据
python inserter.py

# 4. 补充详情页数据（描述+要求）
python enrich_details.py
```

## 数据推送后台（联动）

```
# 把 parsed JSON 导出为标准 CSV
python export_and_push.py

# 导出并直接推送到后台导入接口（需后端已启动）
python export_and_push.py --push
```

## 数据库连接

```
MySQL: localhost:3306
Database: internship_platform
User: root
Password: 通过 DB_PASSWORD 环境变量提供（不要写入文件）
Charset: utf8mb4
```

## 牛客网URL规则

```
列表页: https://www.nowcoder.com/jobs/intern/center?recruitType=2&city=北京
详情页: https://www.nowcoder.com/jobs/detail/{jobId}
```
