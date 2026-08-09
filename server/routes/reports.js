const router = require('express').Router();
const pool = require('../db');
const { requireAuth } = require('../middleware/auth');

// POST /api/reports — 提交反馈/举报（需登录）
router.post('/', requireAuth, async (req, res) => {
  try {
    const { internship_id, type, message } = req.body;
    if (!internship_id || !message) {
      return res.status(400).json({ error: '实习ID和详细说明必填' });
    }

    await pool.query(
      'INSERT INTO reports (user_id, internship_id, type, message) VALUES (?,?,?,?)',
      [req.user.id, internship_id, type || 'other', message]
    );

    res.status(201).json({ message: '反馈已提交，感谢你的贡献！' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
