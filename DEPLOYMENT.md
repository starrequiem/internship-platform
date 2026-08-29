# Railway 上线

本项目使用一个 Express 服务同时提供前端页面、管理后台、API 和上传文件，生产环境不需要单独部署 Cloudflare Pages。

## 1. 创建服务

1. 将仓库连接到 Railway。
2. 在同一 Railway Project 中添加 MySQL。
3. 为应用服务设置下面的变量引用：

```text
NODE_ENV=production
MYSQLHOST=${{MySQL.MYSQLHOST}}
MYSQLPORT=${{MySQL.MYSQLPORT}}
MYSQLUSER=${{MySQL.MYSQLUSER}}
MYSQLPASSWORD=${{MySQL.MYSQLPASSWORD}}
MYSQLDATABASE=${{MySQL.MYSQLDATABASE}}
JWT_SECRET=<至少 32 字符随机值>
ADMIN_JWT_SECRET=<另一段至少 32 字符随机值>
ADMIN_USERNAME=<初始管理员用户名>
ADMIN_PASSWORD=<至少 12 字符的初始管理员密码>
UPLOAD_DIR=/data/uploads
```

Railway 会读取根目录的 `Dockerfile` 和 `railway.json`，部署前自动执行数据库初始化。

## 2. 持久化上传

在应用服务上添加 Volume，挂载路径设置为 `/data`。否则头像和公司 Logo 会在重新部署后丢失。

## 3. 导入现有岗位数据

`npm run db:init` 只创建当前结构、基础标签和初始管理员，不会复制本机数据库中的岗位。要保留本机数据，请通过 `mysqldump` 导出，再使用 Railway MySQL 的公开连接信息导入。

## 4. 验证

- 首页：`/`
- 管理后台：`/admin/`
- 健康检查：`/api/health`

健康检查只有在 MySQL 可连接时才返回 HTTP 200。

## 5. 自定义域名与 Cloudflare

先在 Railway 生成临时域名并验证整站。之后把自定义域名绑定到 Railway，再由 Cloudflare 托管 DNS。前后端使用同一个域名，因此无需额外配置 CORS。

