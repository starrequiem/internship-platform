const router = require('express').Router();
const pool = require('../db');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { requireAuth } = require('../middleware/auth');
const { jwtSecret } = require('../config');

// 内存验证码存储（开发阶段，生产换 Redis）
const captchaStore = new Map(); // username -> { code, expires }

// ---- 公开接口 ----

// GET /api/users/:id — 用户主页
router.get('/:id', async (req, res) => {
  try {
    const [[user]] = await pool.query(
      'SELECT id, username, email, school, major, grade, bio, avatar_url, role, created_at FROM users WHERE id = ?',
      [req.params.id]
    );
    if (!user) return res.status(404).json({ error: '用户不存在' });

    const [[{ share_count }]] = await pool.query(
      'SELECT COUNT(*) AS share_count FROM internships WHERE poster_id = ?', [req.params.id]
    );
    const [[{ thanks_count }]] = await pool.query(
      'SELECT COUNT(*) AS thanks_count FROM thanks WHERE to_user_id = ?', [req.params.id]
    );

    res.json({ ...user, share_count, thanks_count });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/users/:id/internships
router.get('/:id/internships', async (req, res) => {
  try {
    const { page = 1, limit = 20 } = req.query;
    const offset = (parseInt(page) - 1) * parseInt(limit);

    const [rows] = await pool.query(
      `SELECT * FROM internships WHERE poster_id = ? AND status = 'active'
       ORDER BY created_at DESC LIMIT ? OFFSET ?`,
      [req.params.id, parseInt(limit), offset]
    );
    const [[{ total }]] = await pool.query(
      'SELECT COUNT(*) AS total FROM internships WHERE poster_id = ? AND status = ?',
      [req.params.id, 'active']
    );

    res.json({ data: rows, total, page: parseInt(page) });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/users/:id/favorites
router.get('/:id/favorites', async (req, res) => {
  try {
    const { page = 1, limit = 20 } = req.query;
    const offset = (parseInt(page) - 1) * parseInt(limit);

    const [rows] = await pool.query(
      `SELECT i.*, u.username, u.school FROM internships i
       JOIN favorites f ON i.id = f.internship_id
       JOIN users u ON i.poster_id = u.id
       WHERE f.user_id = ? ORDER BY f.created_at DESC
       LIMIT ? OFFSET ?`,
      [req.params.id, parseInt(limit), offset]
    );
    const [[{ total }]] = await pool.query(
      'SELECT COUNT(*) AS total FROM favorites WHERE user_id = ?',
      [req.params.id]
    );

    res.json({ data: rows, total, page: parseInt(page) });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ---- 认证接口 ----

// GET /api/users/me/profile — 当前用户信息（需登录）
router.get('/me/profile', requireAuth, async (req, res) => {
  try {
    const [[user]] = await pool.query(
      'SELECT id, username, email, school, major, grade, bio, avatar_url, role, created_at FROM users WHERE id = ?',
      [req.user.id]
    );
    if (!user) return res.status(404).json({ error: '用户不存在' });
    res.json(user);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/users/captcha — 获取注册验证码
router.post('/captcha', async (req, res) => {
  try {
    const { username } = req.body;
    if (!username || username.length < 2 || username.length > 20) {
      return res.status(400).json({ error: '用户名需2-20个字符' });
    }

    // 检查用户名是否已存在
    const [[existing]] = await pool.query('SELECT id FROM users WHERE username = ?', [username]);
    if (existing) {
      return res.status(409).json({ error: '用户名已存在' });
    }

    // 生成4位验证码
    const code = String(Math.floor(1000 + Math.random() * 9000));
    captchaStore.set(username, { code, expires: Date.now() + 10 * 60 * 1000 });

    console.log(`\n📱 [验证码] 用户名: ${username} | 验证码: ${code} | 10分钟内有效\n`);

    const exposeCaptcha = process.env.EXPOSE_CAPTCHA === 'true';
    res.json({
      message: exposeCaptcha ? '验证码已生成（演示模式）' : '验证码已生成（请查看后端控制台输出）',
      ...(exposeCaptcha ? { captcha: code } : {}),
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/users/register — 注册
router.post('/register', async (req, res) => {
  try {
    const { username, password, captcha, school, major, grade } = req.body;
    if (!username || !password || !captcha) {
      return res.status(400).json({ error: '用户名、密码和验证码必填' });
    }
    if (username.length < 2 || username.length > 20) {
      return res.status(400).json({ error: '用户名需2-20个字符' });
    }
    if (password.length < 6) {
      return res.status(400).json({ error: '密码至少6位' });
    }

    // 验证码校验
    const stored = captchaStore.get(username);
    if (!stored) {
      return res.status(400).json({ error: '请先获取验证码' });
    }
    if (Date.now() > stored.expires) {
      captchaStore.delete(username);
      return res.status(400).json({ error: '验证码已过期，请重新获取' });
    }
    if (stored.code !== String(captcha)) {
      return res.status(400).json({ error: '验证码不正确' });
    }
    captchaStore.delete(username);

    const hash = await bcrypt.hash(password, 10);
    const [result] = await pool.query(
      'INSERT INTO users (username, password_hash, school, major, grade) VALUES (?,?,?,?,?)',
      [username, hash, school || null, major || null, grade || null]
    );

    res.status(201).json({ id: result.insertId, username, message: '注册成功' });
  } catch (err) {
    if (err.code === 'ER_DUP_ENTRY') {
      return res.status(409).json({ error: '用户名已存在' });
    }
    res.status(500).json({ error: err.message });
  }
});

// POST /api/users/login — 登录
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    if (!username || !password) {
      return res.status(400).json({ error: '用户名和密码必填' });
    }

    const [[user]] = await pool.query('SELECT * FROM users WHERE username = ?', [username]);
    if (!user) return res.status(401).json({ error: '用户名或密码错误' });

    const valid = await bcrypt.compare(password, user.password_hash);
    if (!valid) return res.status(401).json({ error: '用户名或密码错误' });

    const token = jwt.sign(
      { id: user.id, username: user.username, role: user.role },
      jwtSecret,
      { expiresIn: '7d' }
    );

    res.json({
      token,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        school: user.school,
        major: user.major,
        grade: user.grade,
        avatar_url: user.avatar_url,
        role: user.role
      }
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/users/profile — 更新个人资料（需登录）
router.put('/profile', requireAuth, async (req, res) => {
  try {
    const { school, major, grade, bio } = req.body;
    await pool.query(
      'UPDATE users SET school = ?, major = ?, grade = ?, bio = ? WHERE id = ?',
      [school || null, major || null, grade || null, bio || null, req.user.id]
    );
    res.json({ message: '资料已更新' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/users/password — 修改密码（需登录，7天内限一次）
router.put('/password', requireAuth, async (req, res) => {
  try {
    const { old_password, new_password } = req.body;
    if (!old_password || !new_password) {
      return res.status(400).json({ error: '旧密码和新密码必填' });
    }
    if (new_password.length < 6) {
      return res.status(400).json({ error: '新密码至少6位' });
    }

    // 验证旧密码
    const [[user]] = await pool.query(
      'SELECT password_hash, password_changed_at FROM users WHERE id = ?', [req.user.id]
    );
    const valid = await bcrypt.compare(old_password, user.password_hash);
    if (!valid) return res.status(400).json({ error: '旧密码不正确' });

    // 检查7天限制
    if (user.password_changed_at) {
      const daysSince = (Date.now() - new Date(user.password_changed_at).getTime()) / (1000 * 60 * 60 * 24);
      if (daysSince < 7) {
        return res.status(400).json({ error: `密码修改后7天内不可再次修改（距离上次修改已过${Math.floor(daysSince)}天）` });
      }
    }

    // 更新密码
    const hash = await bcrypt.hash(new_password, 10);
    await pool.query(
      'UPDATE users SET password_hash = ?, password_changed_at = NOW() WHERE id = ?',
      [hash, req.user.id]
    );

    res.json({ message: '密码已修改' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
