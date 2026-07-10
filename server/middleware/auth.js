/**
 * JWT 认证中间件
 */
const jwt = require('jsonwebtoken');
const JWT_SECRET = 'internship-platform-secret';

const ADMIN_SECRET = 'internship-platform-admin-secret';

/** 解析 token，支持用户和管理员两种密钥 */
function parseToken(token) {
  try { return jwt.verify(token, JWT_SECRET); } catch (_) {}
  try { return jwt.verify(token, ADMIN_SECRET); } catch (_) { return null; }
}

/** 强制认证：无有效 token 返回 401 */
function requireAuth(req, res, next) {
  const auth = req.headers.authorization;
  if (!auth || !auth.startsWith('Bearer ')) {
    return res.status(401).json({ error: '请先登录' });
  }
  const user = parseToken(auth.slice(7));
  if (!user) return res.status(401).json({ error: '登录已过期，请重新登录' });
  req.user = user;
  next();
}

/** 可选认证：有 token 就解析，没有也继续 */
function optionalAuth(req, res, next) {
  const auth = req.headers.authorization;
  if (auth && auth.startsWith('Bearer ')) {
    const user = parseToken(auth.slice(7));
    if (user) req.user = user;
  }
  next();
}

module.exports = { requireAuth, optionalAuth };
