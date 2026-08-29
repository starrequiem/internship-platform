# 上线改造工作记录（2026-08-29）

## 当前目标

将完整项目（原生前端 + Express + MySQL + 管理后台 + 文件上传）改造成可快速部署到 Railway 的单体应用，并保留 Cloudflare 作为后续 DNS/CDN。

## 已完成

- 新增统一生产配置 `server/config.js`，支持 Railway MySQL 变量、动态端口、JWT 密钥、CORS 和上传目录。
- 移除 API、数据库、JWT 的主要硬编码；生产环境缺少 JWT 密钥时拒绝启动。
- Express 同时托管白名单前端页面、管理后台、API 和上传目录，避免公开 `server/sql/docs`。
- 前端与后台 API 地址改为生产同源 `/api`，本地 8080 开发模式仍连接 3000。
- 健康检查加入 MySQL 连通性，支持 Railway 发布健康检查。
- 上传目录支持 `UPLOAD_DIR=/data/uploads`，可挂载 Railway Volume。
- 新增幂等生产数据库基线 `sql/production-schema.sql` 和 `npm run db:init`。
- 管理员初始化不会覆盖已有管理员密码，也不会把同名普通用户直接提升为管理员。
- 新增 Dockerfile、.dockerignore、railway.json、server/.env.example 和 DEPLOYMENT.md。
- 将存在无修复高危漏洞的 `xlsx` 替换为 ExcelJS，并通过 uuid override 清除 npm audit 告警。
- Excel 导入改为支持 CSV/XLSX；XLSX 无效行解析测试通过。
- 维护脚本开始统一读取环境配置。

## 已验证

- 全部 JavaScript 通过 `node --check`。
- `npm audit --omit=dev`：0 vulnerabilities。
- `npm run db:init` 在本机现有 MySQL 上幂等执行成功。
- 本机 3100 端口整站测试：
  - 首页、CSS、公共组件、管理后台：200。
  - `/api/health`：200 且数据库 connected。
  - 岗位列表 API：200。
  - 后台统计和上传未登录：401。
  - `/server/db.js`、`/sql/production-schema.sql`、`/PROMPT.md`：404。
  - `/admin`、`/admin/`、`/admin/index.html` 均为 200。
- XLSX 测试文件解析成功，因缺少必填字段跳过 1 行、插入 0 行。
- Docker 未安装，因此尚未在本机执行镜像构建。

## 尚未完成

1. 提交并同步当前改动到桌面原仓库。
2. 可选安全清理：`维护/爬虫/inserter.py` 和历史文档仍包含旧本机数据库密码文本；主运行服务已不再使用。
3. 安装/登录 Railway CLI，或在 Railway 控制台创建应用服务、MySQL 和 Volume。
4. 配置 Railway 环境变量与随机密钥。
5. 将本机约 5497 条岗位数据导入云端 MySQL（生产初始化脚本默认不复制业务数据）。
6. 构建部署、生成公网域名并进行线上回归。
7. 后续绑定自定义域名和 Cloudflare DNS/CDN。

## 重要路径

- 桌面原仓库：`C:\Users\屠庭宇\Desktop\internship-platform`
- 本次隔离工作克隆：`C:\Users\屠庭宇\.codex\visualizations\2026\08\29\01a04d8b-8340-7a72-a682-89cea1fa9a45\internship-platform-deploy`

