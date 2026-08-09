const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 3000;

// 中间件
app.use(cors());
app.use(express.json({ limit: '1mb' }));
app.use('/uploads', express.static(require('path').join(__dirname, 'uploads')));

// 路由
app.use('/api/internships', require('./routes/internships'));
app.use('/api/users', require('./routes/users'));
app.use('/api/favorites', require('./routes/favorites'));
app.use('/api/tags', require('./routes/tags'));
app.use('/api/applications', require('./routes/applications'));
app.use('/api/thanks', require('./routes/thanks'));
app.use('/api/reports', require('./routes/reports'));
app.use('/api/admin', require('./routes/admin'));
app.use('/api/upload', require('./routes/upload'));

// 健康检查
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', time: new Date().toISOString() });
});

// 404
app.use((req, res) => {
  res.status(404).json({ error: '接口不存在' });
});

// 错误处理
app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({ error: '服务器内部错误' });
});

app.listen(PORT, () => {
  console.log(`🚀 实习通 API 已启动: http://localhost:${PORT}`);
  console.log(`📋 接口文档: http://localhost:${PORT}/api/health`);
});
