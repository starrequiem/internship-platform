const router = require('express').Router();
const pool = require('../db');
const { requireAuth } = require('../middleware/auth');

// POST /api/thanks — 向分享者发送感谢（需登录）
router.post('/', requireAuth, async (req, res) => {
  try {
    const { to_user_id, internship_id, message } = req.body;
    if (!to_user_id) return res.status(400).json({ error: '缺少 to_user_id' });
    if (to_user_id === req.user.id) return res.status(400).json({ error: '不能感谢自己' });

    await pool.query(
      'INSERT INTO thanks (from_user_id, to_user_id, internship_id, message) VALUES (?,?,?,?)',
      [req.user.id, to_user_id, internship_id || null, message || null]
    );
    res.status(201).json({ message: '感谢已发送' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/thanks/received/:userId — 某人收到的感谢
router.get('/received/:userId', async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT t.*, u.username AS from_username, u.avatar_url,
              i.title AS internship_title
       FROM thanks t
       JOIN users u ON t.from_user_id = u.id
       LEFT JOIN internships i ON t.internship_id = i.id
       WHERE t.to_user_id = ?
       ORDER BY t.created_at DESC`,
      [req.params.userId]
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
