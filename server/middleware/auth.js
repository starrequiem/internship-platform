/**
 * JWT 认证中间件
 */
const jwt = require('jsonwebtoken');
const { jwtSecret, adminJwtSecret } = require('../config');

/** 解析 token，支持用户和管理员两种密钥 */
function parseToken(token) {
  try { return jwt.verify(token, jwtSecret); } catch (_) {}
  try { return jwt.verify(token, adminJwtSecret); } catch (_) { return null; }
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

/** 强制管理员：仅管理员 token（role=admin）可通过 */
function requireAdmin(req, res, next) {
  requireAuth(req, res, () => {
    if (req.user && req.user.role === 'admin') return next();
    return res.status(403).json({ error: '需要管理员权限' });
  });
}

module.exports = { requireAuth, optionalAuth, requireAdmin };
