/**
 * 管理员 API
 */
const router = require('express').Router();
const pool = require('../db');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');

const JWT_SECRET = 'internship-platform-admin-secret';

async function adminAuth(req, res, next) {
  const auth = req.headers.authorization;
  if (!auth || !auth.startsWith('Bearer ')) return res.status(401).json({ error: '未授权' });
  try {
    const payload = jwt.verify(auth.slice(7), JWT_SECRET);
    const [[user]] = await pool.query('SELECT id, username, role FROM users WHERE id = ?', [payload.id]);
    if (!user || user.role !== 'admin') return res.status(403).json({ error: '需要管理员权限' });
    req.admin = user;
    next();
  } catch (err) { return res.status(401).json({ error: '登录过期' }); }
}

// 登录
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
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// 仪表盘
router.get('/stats', adminAuth, async (req, res) => {
  try {
    const [[{ total_users }]] = await pool.query('SELECT COUNT(*) AS total_users FROM users');
    const [[{ total_internships }]] = await pool.query('SELECT COUNT(*) AS total_internships FROM internships');
    const [[{ active }]] = await pool.query("SELECT COUNT(*) AS active FROM internships WHERE status='active'");
    const [[{ expired }]] = await pool.query("SELECT COUNT(*) AS expired FROM internships WHERE status='active' AND deadline IS NOT NULL AND deadline < CURDATE()");
    const [[{ today_new }]] = await pool.query('SELECT COUNT(*) AS today_new FROM internships WHERE DATE(created_at) = CURDATE()');
    res.json({ total_users, total_internships, active, expired, today_new });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// 实习列表（含截止日期）
router.get('/internships', adminAuth, async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT i.*, u.username FROM internships i JOIN users u ON i.poster_id = u.id ORDER BY i.created_at DESC LIMIT 200`
    );
    res.json(rows);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// 批量关闭已截止
router.post('/internships/close-expired', adminAuth, async (req, res) => {
  try {
    const [result] = await pool.query(
      "UPDATE internships SET status = 'closed' WHERE status = 'active' AND deadline IS NOT NULL AND deadline < CURDATE()"
    );
    res.json({ message: `已关闭 ${result.affectedRows} 条已截止实习` });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// 编辑实习
router.put('/internships/:id', adminAuth, async (req, res) => {
  try {
    const { title, company, city, job_type, status, deadline, description, contact_info } = req.body;
    await pool.query(
      `UPDATE internships SET title=?, company=?, city=?, job_type=?, status=?, deadline=?, description=?, contact_info=? WHERE id=?`,
      [title, company, city, job_type, status, deadline || null, description || null, contact_info || null, req.params.id]
    );
    res.json({ message: '更新成功' });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// 删除
router.delete('/internships/:id', adminAuth, async (req, res) => {
  try {
    await pool.query('DELETE FROM internships WHERE id = ?', [req.params.id]);
    res.json({ message: '已删除' });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// 用户列表
router.get('/users', adminAuth, async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT u.id, u.username, u.school, u.role, u.created_at,
        (SELECT COUNT(*) FROM internships WHERE poster_id = u.id) AS share_count
       FROM users u ORDER BY u.created_at DESC`
    );
    res.json(rows);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

module.exports = router;
