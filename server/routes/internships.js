const router = require('express').Router();
const pool = require('../db');
const { requireAuth, optionalAuth } = require('../middleware/auth');

// GET /api/internships — 列表（公开）
router.get('/', async (req, res) => {
  try {
    const { page = 1, limit = 20, city, job_type, major, keyword, sort = 'latest' } = req.query;
    const offset = (parseInt(page) - 1) * parseInt(limit);

    let where = ['i.status = ?'];
    let params = ['active'];

    if (city)     { where.push('i.city = ?');       params.push(city); }
    if (job_type) { where.push('i.job_type = ?');    params.push(job_type); }
    if (major)    { where.push('(i.target_major LIKE ? OR i.target_major = ?)'); params.push(`%${major}%`, '不限专业'); }
    if (keyword)  {
      where.push(`(i.title LIKE ? OR i.company LIKE ? OR i.description LIKE ? OR i.city LIKE ? OR i.district LIKE ? OR i.job_type LIKE ? OR i.target_major LIKE ? OR i.requirements LIKE ? OR i.id IN (SELECT it.internship_id FROM internship_tags it JOIN tags t ON it.tag_id = t.id WHERE t.name LIKE ?))`);
      const kw = `%${keyword}%`;
      params.push(kw, kw, kw, kw, kw, kw, kw, kw, kw);
    }

    const orderMap = {
      latest:   'i.created_at DESC',
      salary:   'i.salary_max DESC',
      deadline: 'i.deadline ASC',
      popular:  'i.favorite_count DESC',
    };
    const order = orderMap[sort] || orderMap.latest;

    const [rows] = await pool.query(
      `SELECT i.*, u.username, u.school, u.avatar_url AS poster_avatar
       FROM internships i JOIN users u ON i.poster_id = u.id
       WHERE ${where.join(' AND ')}
       ORDER BY ${order}
       LIMIT ? OFFSET ?`,
      [...params, parseInt(limit), offset]
    );

    const [[{ total }]] = await pool.query(
      `SELECT COUNT(*) AS total FROM internships i WHERE ${where.join(' AND ')}`,
      params
    );

    // 批量获取所有实习的标签
    const ids = rows.map(r => r.id);
    if (ids.length) {
      const [tagRows] = await pool.query(
        `SELECT it.internship_id, t.name FROM internship_tags it JOIN tags t ON it.tag_id = t.id WHERE it.internship_id IN (?)`,
        [ids]
      );
      const tagMap = {};
      tagRows.forEach(tr => {
        if (!tagMap[tr.internship_id]) tagMap[tr.internship_id] = [];
        tagMap[tr.internship_id].push(tr.name);
      });
      rows.forEach(r => { r.tags = tagMap[r.id] || []; });
    }

    res.json({ data: rows, total, page: parseInt(page), limit: parseInt(limit) });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

// GET /api/internships/hot — 热门排行（公开）
router.get('/hot/list', async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT i.id, i.title, i.company, i.city, i.salary_min, i.salary_max, i.favorite_count
       FROM internships i WHERE i.status = 'active' AND i.created_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
       ORDER BY i.favorite_count DESC LIMIT 10`
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/internships/urgent — 即将截止（公开）
router.get('/urgent/list', async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT id, title, company, deadline FROM internships
       WHERE status = 'active' AND deadline IS NOT NULL AND deadline >= CURDATE()
       ORDER BY deadline ASC LIMIT 10`
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/internships/:id — 详情（公开，可选认证用于判断收藏状态）
router.get('/:id', optionalAuth, async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT i.*, u.username, u.school, u.major, u.avatar_url AS poster_avatar
       FROM internships i JOIN users u ON i.poster_id = u.id
       WHERE i.id = ?`, [req.params.id]
    );
    if (!rows.length) return res.status(404).json({ error: '岗位不存在' });

    // 增加浏览次数
    await pool.query('UPDATE internships SET view_count = view_count + 1 WHERE id = ?', [req.params.id]);

    // 获取标签
    const [tags] = await pool.query(
      `SELECT t.name FROM tags t
       JOIN internship_tags it ON t.id = it.tag_id
       WHERE it.internship_id = ?`, [req.params.id]
    );

    const result = { ...rows[0], tags: tags.map(t => t.name) };

    // 如果已登录，返回收藏状态
    if (req.user) {
      const [[fav]] = await pool.query(
        'SELECT id FROM favorites WHERE user_id = ? AND internship_id = ?',
        [req.user.id, req.params.id]
      );
      result.is_favorited = !!fav;
    }

    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/internships — 发布（需登录）
router.post('/', requireAuth, async (req, res) => {
  try {
    const { title, company, city, district, job_type, salary_min, salary_max,
            education, days_per_week, duration_months, target_grade, target_major,
            headcount, deadline, description, requirements, apply_url, apply_email,
            can_refer, tags } = req.body;

    if (!title || !company || !city || !job_type) {
      return res.status(400).json({ error: '必填字段：title, company, city, job_type' });
    }

    const [result] = await pool.query(
      `INSERT INTO internships (poster_id, title, company, city, district, job_type, salary_min, salary_max,
        education, days_per_week, duration_months, target_grade, target_major,
        headcount, deadline, description, requirements, apply_url, apply_email, can_refer)
       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
      [req.user.id, title, company, city, district || null, job_type,
       salary_min || null, salary_max || null,
       education || '本科及以上', days_per_week || 4, duration_months || 3,
       target_grade || null, target_major || null,
       headcount || 1, deadline || null, description || null, requirements || null,
       apply_url || null, apply_email || null, can_refer ? 1 : 0]
    );

    // 关联标签（支持标签名或ID）
    if (tags && tags.length) {
      for (const tag of tags) {
        try {
          if (typeof tag === 'string') {
            await pool.query('INSERT IGNORE INTO tags (name) VALUES (?)', [tag]);
            const [[t]] = await pool.query('SELECT id FROM tags WHERE name = ?', [tag]);
            if (t) await pool.query('INSERT IGNORE INTO internship_tags VALUES (?, ?)', [result.insertId, t.id]);
          } else {
            await pool.query('INSERT IGNORE INTO internship_tags VALUES (?, ?)', [result.insertId, tag]);
          }
        } catch (_) { /* 跳过单个标签失败 */ }
      }
    }

    res.status(201).json({ id: result.insertId, message: '发布成功' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/internships/:id — 编辑实习（仅发布者本人）
router.put('/:id', requireAuth, async (req, res) => {
  try {
    const [[intern]] = await pool.query('SELECT poster_id, status FROM internships WHERE id = ?', [req.params.id]);
    if (!intern) return res.status(404).json({ error: '岗位不存在' });
    if (intern.poster_id !== req.user.id) return res.status(403).json({ error: '只能编辑自己发布的实习' });

    const { title, company, city, district, job_type, salary_min, salary_max,
            education, days_per_week, duration_months, target_grade, target_major,
            headcount, deadline, description, requirements, apply_url, apply_email,
            can_refer, tags } = req.body;

    if (!title || !company || !city || !job_type) {
      return res.status(400).json({ error: '必填字段：title, company, city, job_type' });
    }

    await pool.query(
      `UPDATE internships SET
        title = ?, company = ?, city = ?, district = ?, job_type = ?,
        salary_min = ?, salary_max = ?, education = ?, days_per_week = ?,
        duration_months = ?, target_grade = ?, target_major = ?,
        headcount = ?, deadline = ?, description = ?, requirements = ?,
        apply_url = ?, apply_email = ?, can_refer = ?
       WHERE id = ?`,
      [title, company, city, district || null, job_type,
       salary_min || null, salary_max || null,
       education || '本科及以上', days_per_week || 4, duration_months || 3,
       target_grade || null, target_major || null,
       headcount || 1, deadline || null, description || null, requirements || null,
       apply_url || null, apply_email || null, can_refer ? 1 : 0,
       req.params.id]
    );

    // 更新标签（先删后插）
    if (tags !== undefined) {
      await pool.query('DELETE FROM internship_tags WHERE internship_id = ?', [req.params.id]);
      if (tags && tags.length) {
        for (const tag of tags) {
          // 支持标签名或标签ID
          if (typeof tag === 'string') {
            await pool.query('INSERT IGNORE INTO tags (name) VALUES (?)', [tag]);
            const [[t]] = await pool.query('SELECT id FROM tags WHERE name = ?', [tag]);
            if (t) await pool.query('INSERT IGNORE INTO internship_tags VALUES (?, ?)', [req.params.id, t.id]);
          } else {
            await pool.query('INSERT IGNORE INTO internship_tags VALUES (?, ?)', [req.params.id, tag]);
          }
        }
      }
    }

    // 返回更新后的数据
    const [[updated]] = await pool.query('SELECT * FROM internships WHERE id = ?', [req.params.id]);
    res.json({ message: '修改已保存', data: updated });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/internships/:id/close — 关闭实习（仅发布者本人）
router.put('/:id/close', requireAuth, async (req, res) => {
  try {
    const [[intern]] = await pool.query('SELECT poster_id, status FROM internships WHERE id = ?', [req.params.id]);
    if (!intern) return res.status(404).json({ error: '岗位不存在' });
    if (intern.poster_id !== req.user.id) return res.status(403).json({ error: '只能关闭自己发布的实习' });

    await pool.query("UPDATE internships SET status = 'closed' WHERE id = ?", [req.params.id]);
    res.json({ message: '实习已关闭' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
