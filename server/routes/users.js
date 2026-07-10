const router = require('express').Router();
const pool = require('../db');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { requireAuth } = require('../middleware/auth');

const JWT_SECRET = 'internship-platform-secret';

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
    const [[{ fav_count }]] = await pool.query(
      'SELECT COUNT(*) AS fav_count FROM favorites WHERE user_id = ?', [req.params.id]
    );
    const [[{ thanks_count }]] = await pool.query(
      'SELECT COUNT(*) AS thanks_count FROM thanks WHERE to_user_id = ?', [req.params.id]
    );

    res.json({ ...user, share_count, fav_count, thanks_count });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/users/:id/internships — 用户分享的实习（支持分页）
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

// GET /api/users/:id/favorites — 用户收藏的实习（支持分页）
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

// GET /api/users/me — 获取当前登录用户信息（需登录）
router.get('/me/profile', requireAuth, async (req, res) => {
  try {
    const [[user]] = await pool.query(
      'SELECT id, username, email, school, major, grade, bio, avatar_url, role, is_member, email_verified, created_at FROM users WHERE id = ?',
      [req.user.id]
    );
    if (!user) return res.status(404).json({ error: '用户不存在' });
    res.json(user);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/users/register — 注册
router.post('/register', async (req, res) => {
  try {
    const { username, password, email, school, major, grade } = req.body;
    if (!username || !password) {
      return res.status(400).json({ error: '用户名和密码必填' });
    }
    if (username.length < 2 || username.length > 20) {
      return res.status(400).json({ error: '用户名需2-20个字符' });
    }
    if (password.length < 6) {
      return res.status(400).json({ error: '密码至少6位' });
    }

    const hash = await bcrypt.hash(password, 10);
    const [result] = await pool.query(
      'INSERT INTO users (username, password_hash, email, school, major, grade) VALUES (?,?,?,?,?,?)',
      [username, hash, email || null, school || null, major || null, grade || null]
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
      { id: user.id, username: user.username },
      JWT_SECRET,
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
        role: user.role,
        is_member: user.is_member || 0,
        email_verified: user.email_verified || 0,
      }
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/users/profile — 更新个人资料（需登录）
router.put('/profile', requireAuth, async (req, res) => {
  try {
    const { school, major, grade, bio, email } = req.body;
    await pool.query(
      'UPDATE users SET school = ?, major = ?, grade = ?, bio = ?, email = COALESCE(?, email) WHERE id = ?',
      [school || null, major || null, grade || null, bio || null, email || null, req.user.id]
    );
    res.json({ message: '资料已更新' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ---- 邮箱绑定（验证码模式） ----

// 内存存储验证码（正式上线后替换为 Redis/数据库 + 邮件发送）
const verifyCodes = new Map(); // email -> { code, expires }

// POST /api/users/bind-email/send-code — 发送验证码（需登录）
router.post('/bind-email/send-code', requireAuth, async (req, res) => {
  try {
    const { email } = req.body;
    if (!email) return res.status(400).json({ error: '请输入邮箱地址' });

    // 生成6位验证码
    const code = String(Math.floor(100000 + Math.random() * 900000));
    verifyCodes.set(email, { code, expires: Date.now() + 10 * 60 * 1000 }); // 10分钟有效

    // TODO: 正式上线时接入邮件发送服务（如 SendGrid / 阿里云邮件推送）
    console.log(`\n📧 [验证码] 邮箱: ${email} | 验证码: ${code} | 10分钟内有效\n`);

    res.json({ message: '验证码已发送（开发阶段请查看控制台输出）' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/users/bind-email/verify — 验证邮箱并升级会员（需登录）
router.post('/bind-email/verify', requireAuth, async (req, res) => {
  try {
    const { email, code } = req.body;
    if (!email || !code) return res.status(400).json({ error: '邮箱和验证码必填' });

    const stored = verifyCodes.get(email);
    if (!stored) return res.status(400).json({ error: '请先获取验证码' });
    if (Date.now() > stored.expires) {
      verifyCodes.delete(email);
      return res.status(400).json({ error: '验证码已过期，请重新获取' });
    }
    if (stored.code !== String(code)) {
      return res.status(400).json({ error: '验证码不正确' });
    }

    verifyCodes.delete(email);

    // 更新邮箱并升级为会员
    await pool.query(
      'UPDATE users SET email = ?, email_verified = 1, is_member = 1 WHERE id = ?',
      [email, req.user.id]
    );

    res.json({ message: '邮箱绑定成功！您已升级为会员，可以发布和评论实习信息了 🎉' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/users/password — 修改密码（需登录）
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
    const [[user]] = await pool.query('SELECT password_hash FROM users WHERE id = ?', [req.user.id]);
    const valid = await bcrypt.compare(old_password, user.password_hash);
    if (!valid) return res.status(400).json({ error: '旧密码不正确' });

    // 更新密码
    const hash = await bcrypt.hash(new_password, 10);
    await pool.query('UPDATE users SET password_hash = ? WHERE id = ?', [hash, req.user.id]);

    res.json({ message: '密码已修改' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ---- 忘记密码 ----

// POST /api/users/forgot-password — 发送重置验证码（公开）
router.post('/forgot-password', async (req, res) => {
  try {
    const { email, username } = req.body;
    if (!email || !username) return res.status(400).json({ error: '请输入用户名和注册邮箱' });

    const [[user]] = await pool.query(
      'SELECT id FROM users WHERE username = ? AND email = ?', [username, email]
    );
    if (!user) return res.status(404).json({ error: '用户名与邮箱不匹配' });

    const code = String(Math.floor(100000 + Math.random() * 900000));
    verifyCodes.set(email, { code, expires: Date.now() + 10 * 60 * 1000, userId: user.id, type: 'reset' });

    console.log(`\n🔑 [密码重置] 用户名: ${username} | 邮箱: ${email} | 验证码: ${code} | 10分钟内有效\n`);
    res.json({ message: '重置验证码已发送（开发阶段请查看控制台输出）' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/users/reset-password — 验证并重置密码（公开）
router.post('/reset-password', async (req, res) => {
  try {
    const { email, code, new_password } = req.body;
    if (!email || !code || !new_password) return res.status(400).json({ error: '邮箱、验证码和新密码必填' });
    if (new_password.length < 6) return res.status(400).json({ error: '新密码至少6位' });

    const stored = verifyCodes.get(email);
    if (!stored || stored.type !== 'reset') return res.status(400).json({ error: '请先获取验证码' });
    if (Date.now() > stored.expires) {
      verifyCodes.delete(email);
      return res.status(400).json({ error: '验证码已过期，请重新获取' });
    }
    if (stored.code !== String(code)) return res.status(400).json({ error: '验证码不正确' });

    verifyCodes.delete(email);
    const hash = await bcrypt.hash(new_password, 10);
    await pool.query('UPDATE users SET password_hash = ? WHERE id = ?', [hash, stored.userId]);

    res.json({ message: '密码重置成功，请使用新密码登录' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
