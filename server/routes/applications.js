const router = require('express').Router();
const pool = require('../db');
const { requireAuth } = require('../middleware/auth');

// POST /api/applications — 记录投递（需登录+会员）
router.post('/', requireAuth, async (req, res) => {
  try {
    const { internship_id } = req.body;
    if (!internship_id) return res.status(400).json({ error: '缺少 internship_id' });

    // 检查会员权限
    const [[user]] = await pool.query('SELECT is_member, role FROM users WHERE id = ?', [req.user.id]);
    if (user.role !== 'admin' && !user.is_member) {
      return res.status(403).json({ error: '请先绑定邮箱升级会员' });
    }

    try {
      await pool.query(
        'INSERT INTO applications (user_id, internship_id) VALUES (?,?)',
        [req.user.id, internship_id]
      );
      res.status(201).json({ message: '投递记录已保存' });
    } catch (err) {
      if (err.code === 'ER_DUP_ENTRY') {
        return res.json({ message: '已投递过该岗位' });
      }
      throw err;
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/applications — 我的投递列表（需登录）
router.get('/', requireAuth, async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT a.*, i.title, i.company, i.city, i.salary_min, i.salary_max, i.status AS intern_status
       FROM applications a
       JOIN internships i ON a.internship_id = i.id
       WHERE a.user_id = ?
       ORDER BY a.created_at DESC`,
      [req.user.id]
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
