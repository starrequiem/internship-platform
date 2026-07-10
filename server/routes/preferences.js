const router = require('express').Router();
const pool = require('../db');
const { requireAuth } = require('../middleware/auth');

// GET /api/users/:id/preferences — 获取用户偏好标签（公开）
router.get('/:id/preferences', async (req, res) => {
  try {
    const [rows] = await pool.query(
      'SELECT id, tag_name, created_at FROM user_tag_preferences WHERE user_id = ? ORDER BY created_at DESC',
      [req.params.id]
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/users/:id/preferences — 添加偏好标签（需登录，只能操作自己）
router.post('/:id/preferences', requireAuth, async (req, res) => {
  try {
    if (parseInt(req.params.id) !== req.user.id) {
      return res.status(403).json({ error: '只能修改自己的偏好标签' });
    }
    const { tag_name } = req.body;
    if (!tag_name || !tag_name.trim()) {
      return res.status(400).json({ error: '标签名不能为空' });
    }
    await pool.query(
      'INSERT IGNORE INTO user_tag_preferences (user_id, tag_name) VALUES (?, ?)',
      [req.user.id, tag_name.trim()]
    );
    res.status(201).json({ message: '已添加' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// DELETE /api/users/:id/preferences/:tagName — 删除偏好标签（需登录，只能操作自己）
router.delete('/:id/preferences/:tagName', requireAuth, async (req, res) => {
  try {
    if (parseInt(req.params.id) !== req.user.id) {
      return res.status(403).json({ error: '只能修改自己的偏好标签' });
    }
    await pool.query(
      'DELETE FROM user_tag_preferences WHERE user_id = ? AND tag_name = ?',
      [req.user.id, req.params.tagName]
    );
    res.json({ message: '已删除' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
