const router = require('express').Router();
const pool = require('../db');
const { requireAuth } = require('../middleware/auth');

// GET /api/notifications — 通知列表（需登录）
router.get('/', requireAuth, async (req, res) => {
  try {
    const { unread_only } = req.query;
    let sql = 'SELECT * FROM notifications WHERE user_id = ?';
    if (unread_only === '1') sql += ' AND is_read = 0';
    sql += ' ORDER BY created_at DESC LIMIT 50';
    const [rows] = await pool.query(sql, [req.user.id]);
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/notifications/unread-count — 未读数（需登录）
router.get('/unread-count', requireAuth, async (req, res) => {
  try {
    const [[{ count }]] = await pool.query(
      'SELECT COUNT(*) AS count FROM notifications WHERE user_id = ? AND is_read = 0',
      [req.user.id]
    );
    res.json({ count });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/notifications/:id/read — 标记已读（需登录）
router.put('/:id/read', requireAuth, async (req, res) => {
  try {
    await pool.query(
      'UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?',
      [req.params.id, req.user.id]
    );
    res.json({ message: 'ok' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/notifications/read-all — 全部已读（需登录）
router.put('/read-all', requireAuth, async (req, res) => {
  try {
    await pool.query(
      'UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0',
      [req.user.id]
    );
    res.json({ message: '已全部标记为已读' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
