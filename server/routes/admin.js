/**
 * 管理员 API（内部使用，不对外开放）
 */
const router = require('express').Router();
const pool = require('../db');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');

const JWT_SECRET = 'internship-platform-admin-secret';

// ---- 管理员认证中间件 ----
async function adminAuth(req, res, next) {
  const auth = req.headers.authorization;
  if (!auth || !auth.startsWith('Bearer ')) {
    return res.status(401).json({ error: '未授权访问' });
  }
  try {
    const payload = jwt.verify(auth.slice(7), JWT_SECRET);
    const [[user]] = await pool.query('SELECT id, username, role FROM users WHERE id = ?', [payload.id]);
    if (!user || user.role !== 'admin') {
      return res.status(403).json({ error: '需要管理员权限' });
    }
    req.admin = user;
    next();
  } catch (err) {
    return res.status(401).json({ error: '登录已过期，请重新登录' });
  }
}

// ---- 管理员登录 ----
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    const [[user]] = await pool.query('SELECT * FROM users WHERE username = ?', [username]);
    if (!user) return res.status(401).json({ error: '用户名或密码错误' });

    const valid = await bcrypt.compare(password, user.password_hash);
    if (!valid) return res.status(401).json({ error: '用户名或密码错误' });

    if (user.role !== 'admin') return res.status(403).json({ error: '无管理员权限' });

    const token = jwt.sign({ id: user.id, username: user.username, role: 'admin' }, JWT_SECRET, { expiresIn: '12h' });
    res.json({ token, admin: { id: user.id, username: user.username } });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ---- 仪表盘统计 ----
router.get('/stats', adminAuth, async (req, res) => {
  try {
    const [[{ total_users }]]       = await pool.query('SELECT COUNT(*) AS total_users FROM users');
    const [[{ total_internships }]] = await pool.query('SELECT COUNT(*) AS total_internships FROM internships');
    const [[{ active_internships }]]= await pool.query("SELECT COUNT(*) AS active_internships FROM internships WHERE status='active'");
    const [[{ total_favorites }]]   = await pool.query('SELECT COUNT(*) AS total_favorites FROM favorites');
    const [[{ total_tags }]]        = await pool.query('SELECT COUNT(*) AS total_tags FROM tags');
    const [[{ today_new }]]         = await pool.query('SELECT COUNT(*) AS today_new FROM internships WHERE DATE(created_at) = CURDATE()');

    res.json({
      total_users, total_internships, active_internships,
      total_favorites, total_tags, today_new
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ---- 实习管理 ----
router.get('/internships', adminAuth, async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT i.*, u.username, u.school FROM internships i
       JOIN users u ON i.poster_id = u.id
       ORDER BY i.created_at DESC`
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.put('/internships/:id', adminAuth, async (req, res) => {
  try {
    const { title, company, city, district, job_type, status, salary_min, salary_max,
            education, headcount, deadline, target_major, target_grade,
            description, requirements, apply_url, apply_email } = req.body;
    await pool.query(
      `UPDATE internships SET title=?, company=?, city=?, district=?, job_type=?, status=?,
       salary_min=?, salary_max=?, education=?, headcount=?, deadline=?,
       target_major=?, target_grade=?, description=?, requirements=?,
       apply_url=?, apply_email=? WHERE id=?`,
      [title, company, city, district || null, job_type, status,
       salary_min || null, salary_max || null, education,
       headcount || null, deadline || null,
       target_major || null, target_grade || null,
       description || null, requirements || null,
       apply_url || null, apply_email || null, req.params.id]
    );
    res.json({ message: '更新成功' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.delete('/internships/:id', adminAuth, async (req, res) => {
  try {
    await pool.query('DELETE FROM internships WHERE id = ?', [req.params.id]);
    res.json({ message: '已删除' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ---- 用户管理 ----
router.get('/users', adminAuth, async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT u.id, u.username, u.email, u.school, u.major, u.role, u.created_at,
        (SELECT COUNT(*) FROM internships WHERE poster_id = u.id) AS share_count
       FROM users u ORDER BY u.created_at DESC`
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.put('/users/:id', adminAuth, async (req, res) => {
  try {
    const { role } = req.body;
    await pool.query('UPDATE users SET role = ? WHERE id = ?', [role, req.params.id]);
    res.json({ message: '更新成功' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
