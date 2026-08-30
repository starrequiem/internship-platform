const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const pool = require('./db');
const config = require('./config');

const app = express();

if (config.isProduction) app.set('trust proxy', 1);

app.disable('x-powered-by');
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'SAMEORIGIN');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  next();
});
app.use(cors({
  origin(origin, callback) {
    if (!origin || config.corsOrigins.includes(origin) || /^https:\/\/internship-platform-production-80c3\.up\.railway\.app$/.test(origin)) return callback(null, true);
    const error = new Error('该请求来源未被允许');
    error.status = 403;
    return callback(error);
  },
}));
app.use(express.json({ limit: '1mb' }));

fs.mkdirSync(config.uploadDir, { recursive: true });
app.use('/uploads', express.static(config.uploadDir, { dotfiles: 'deny', maxAge: '1d' }));

app.use('/api/internships', require('./routes/internships'));
app.use('/api/users', require('./routes/users'));
app.use('/api/favorites', require('./routes/favorites'));
app.use('/api/tags', require('./routes/tags'));
app.use('/api/applications', require('./routes/applications'));
app.use('/api/thanks', require('./routes/thanks'));
app.use('/api/reports', require('./routes/reports'));
app.use('/api/admin', require('./routes/admin'));
app.use('/api/upload', require('./routes/upload'));

app.get('/api/health', async (req, res) => {
  try {
    await pool.query('SELECT 1');
    res.json({ status: 'ok', database: 'connected', time: new Date().toISOString() });
  } catch (err) {
    res.status(503).json({ status: 'error', database: 'unavailable' });
  }
});

app.use('/api', (req, res) => {
  res.status(404).json({ error: '接口不存在' });
});

// 只暴露前端需要的白名单资源，避免 server/sql/docs 被公开。
for (const directory of ['css', 'js', 'components']) {
  app.use(`/${directory}`, express.static(path.join(config.frontendRoot, directory), {
    dotfiles: 'deny',
    maxAge: config.isProduction ? '1h' : 0,
  }));
}

const publicPages = new Set([
  'about.html', 'detail.html', 'edit.html', 'index.html', 'login.html',
  'privacy.html', 'profile.html', 'register.html', 'search.html', 'terms.html',
]);

app.get('/', (req, res) => res.sendFile(path.join(config.frontendRoot, 'index.html')));
app.get(['/admin', '/admin/', '/admin/index.html'], (req, res) => {
  res.sendFile(path.join(config.frontendRoot, 'admin', 'index.html'));
});
app.get('/:page', (req, res, next) => {
  if (!publicPages.has(req.params.page)) return next();
  return res.sendFile(path.join(config.frontendRoot, req.params.page));
});

app.use((req, res) => {
  res.status(404).type('text').send('页面不存在');
});

app.use((err, req, res, next) => {
  if (res.headersSent) return next(err);
  const status = err.status || 500;
  if (status >= 500) console.error(err);
  return res.status(status).json({ error: status === 500 ? '服务器内部错误' : err.message });
});

const server = app.listen(config.port, '0.0.0.0', () => {
  console.log(`🚀 实习通已启动: http://localhost:${config.port}`);
  console.log(`📋 健康检查: http://localhost:${config.port}/api/health`);
});

async function shutdown(signal) {
  console.log(`\n收到 ${signal}，正在关闭服务...`);
  server.close(async () => {
    await pool.end();
    process.exit(0);
  });
  setTimeout(() => process.exit(1), 10000).unref();
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

module.exports = app;

