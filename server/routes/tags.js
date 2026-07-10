const router = require('express').Router();
const pool = require('../db');

// GET /api/tags — 获取全部标签
router.get('/', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM tags ORDER BY id');
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
