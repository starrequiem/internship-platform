const router = require('express').Router();
const pool = require('../db');
const { requireAuth } = require('../middleware/auth');

// POST /api/subscriptions — 创建订阅（需登录）
router.post('/', requireAuth, async (req, res) => {
  try {
    const { keyword, city, job_type, major } = req.body;
    await pool.query(
      'INSERT INTO subscriptions (user_id, keyword, city, job_type, major) VALUES (?,?,?,?,?)',
      [req.user.id, keyword || null, city || null, job_type || null, major || null]
    );
    res.status(201).json({ message: '订阅成功' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// DELETE /api/subscriptions/:id — 取消订阅（需登录）
router.delete('/:id', requireAuth, async (req, res) => {
  try {
    await pool.query(
      'UPDATE subscriptions SET is_active = 0 WHERE id = ? AND user_id = ?',
      [req.params.id, req.user.id]
    );
    res.json({ message: '已取消' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/subscriptions — 获取当前用户订阅（需登录）
router.get('/', requireAuth, async (req, res) => {
  try {
    const [rows] = await pool.query(
      'SELECT * FROM subscriptions WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC',
      [req.user.id]
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
