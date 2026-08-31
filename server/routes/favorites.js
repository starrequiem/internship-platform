const router = require('express').Router();
const pool = require('../db');
const { requireAuth } = require('../middleware/auth');

// POST /api/favorites — 收藏（需登录，从 token 取 user_id）
router.post('/', requireAuth, async (req, res) => {
  try {
    const { internship_id } = req.body;
    if (!internship_id) return res.status(400).json({ error: '缺少 internship_id' });

    const [result] = await pool.query('INSERT IGNORE INTO favorites (user_id, internship_id) VALUES (?,?)',
      [req.user.id, internship_id]);
    if (result.affectedRows) {
      await pool.query('UPDATE internships SET favorite_count = favorite_count + 1 WHERE id = ?',
        [internship_id]);
    }
    res.json({ message: '已收藏' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// DELETE /api/favorites — 取消收藏（需登录）
router.delete('/', requireAuth, async (req, res) => {
  try {
    const { internship_id } = req.body;
    if (!internship_id) return res.status(400).json({ error: '缺少 internship_id' });

    const [result] = await pool.query('DELETE FROM favorites WHERE user_id = ? AND internship_id = ?',
      [req.user.id, internship_id]);
    if (result.affectedRows) {
      await pool.query('UPDATE internships SET favorite_count = GREATEST(favorite_count - 1, 0) WHERE id = ?',
        [internship_id]);
    }
    res.json({ message: '已取消' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/favorites/check?internship_id= — 检查是否收藏（需登录）
router.get('/check', requireAuth, async (req, res) => {
  try {
    const [rows] = await pool.query(
      'SELECT id FROM favorites WHERE user_id = ? AND internship_id = ?',
      [req.user.id, req.query.internship_id]
    );
    res.json({ favorited: rows.length > 0 });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
