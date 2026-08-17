/**
 * 管理员 API
 */
const router = require('express').Router();
const pool = require('../db');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const multer = require('multer');
const XLSX = require('xlsx');
const path = require('path');
const iconv = require('iconv-lite');

const JWT_SECRET = 'internship-platform-admin-secret';

async function adminAuth(req, res, next) {
  const auth = req.headers.authorization;
  if (!auth || !auth.startsWith('Bearer ')) return res.status(401).json({ error: '未授权' });
  try {
    const payload = jwt.verify(auth.slice(7), JWT_SECRET);
    const [[user]] = await pool.query('SELECT id, username, role FROM users WHERE id = ?', [payload.id]);
    if (!user || user.role !== 'admin') return res.status(403).json({ error: '需要管理员权限' });
    req.admin = user;
    next();
  } catch (err) { return res.status(401).json({ error: '登录过期' }); }
}

// 批量导入：文件上传（内存存储）
const importUpload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 },
});

// CSV/Excel 表头 → 字段名 映射（中英文均可）
const HEADER_MAP = {
  '岗位名称': 'title', '岗位': 'title', '职位名称': 'title', 'title': 'title',
  '公司名称': 'company', '公司': 'company', 'company': 'company',
  '工作城市': 'city', '城市': 'city', 'city': 'city',
  '详细地址': 'district', '地址': 'district', '区域': 'district', 'district': 'district',
  '岗位类型': 'job_type', '职位类型': 'job_type', '类型': 'job_type', 'job_type': 'job_type',
  '最低薪资': 'salary_min', '薪资下限': 'salary_min', 'salary_min': 'salary_min',
  '最高薪资': 'salary_max', '薪资上限': 'salary_max', 'salary_max': 'salary_max',
  '学历要求': 'education', '学历': 'education', 'education': 'education',
  '每周出勤': 'days_per_week', '出勤天数': 'days_per_week', 'days_per_week': 'days_per_week',
  '实习时长': 'duration_months', '实习月数': 'duration_months', 'duration_months': 'duration_months',
  '面向年级': 'target_grade', '年级': 'target_grade', 'target_grade': 'target_grade',
  '面向专业': 'target_major', '专业': 'target_major', 'target_major': 'target_major',
  '招聘人数': 'headcount', '人数': 'headcount', 'headcount': 'headcount',
  '截止日期': 'deadline', '投递截止': 'deadline', 'deadline': 'deadline',
  '投递时间': 'apply_time', 'apply_time': 'apply_time',
  '职位描述': 'description', '岗位描述': 'description', '描述': 'description', 'description': 'description',
  '任职要求': 'requirements', '岗位要求': 'requirements', '要求': 'requirements', 'requirements': 'requirements',
  '联系信息': 'contact_info', '联系方式': 'contact_info', '投递方式': 'contact_info', 'contact_info': 'contact_info',
  '标签': 'tags', '技术标签': 'tags', 'tags': 'tags',
};

function decodeBuffer(buf) {
  if (buf.length >= 3 && buf[0] === 0xEF && buf[1] === 0xBB && buf[2] === 0xBF) {
    return buf.slice(3).toString('utf8');
  }
  if (buf.length >= 2 && buf[0] === 0xFF && buf[1] === 0xFE) {
    return buf.toString('utf16le').replace(/^﻿/, '');
  }
  const utf8 = buf.toString('utf8');
  if (utf8.includes('�')) return iconv.decode(buf, 'gbk');
  return utf8;
}

function parseCSV(text) {
  const rows = [];
  let row = [], field = '', inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else inQuotes = false;
      } else field += c;
    } else {
      if (c === '"') inQuotes = true;
      else if (c === ',') { row.push(field); field = ''; }
      else if (c === '\n' || c === '\r') {
        if (c === '\r' && text[i + 1] === '\n') i++;
        row.push(field); field = '';
        if (row.some(x => String(x).trim() !== '')) rows.push(row);
        row = [];
      } else field += c;
    }
  }
  row.push(field);
  if (row.some(x => String(x).trim() !== '')) rows.push(row);
  return rows;
}

function normalizeDate(v) {
  if (v === undefined || v === null || v === '') return null;
  if (v instanceof Date) {
    const y = v.getFullYear(), m = String(v.getMonth() + 1).padStart(2, '0'), d = String(v.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }
  if (typeof v === 'number') { // Excel 序列日期
    const d = new Date(Math.round((v - 25569) * 86400 * 1000));
    return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(d.getUTCDate()).padStart(2, '0')}`;
  }
  const s = String(v).trim();
  const m = s.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/);
  if (m) return `${m[1]}-${m[2].padStart(2, '0')}-${m[3].padStart(2, '0')}`;
  return s;
}

function mapRow(row) {
  const d = {};
  for (const key in row) {
    const field = HEADER_MAP[String(key).trim()];
    if (field) d[field] = row[key];
  }
  if (typeof d.tags === 'string') {
    d.tags = d.tags.split(/[,，;；]/).map(s => s.trim()).filter(Boolean);
  } else if (!Array.isArray(d.tags)) {
    d.tags = [];
  }
  for (const k of ['salary_min', 'salary_max', 'days_per_week', 'duration_months', 'headcount']) {
    if (d[k] === undefined || d[k] === null || d[k] === '') { d[k] = null; continue; }
    const n = parseInt(d[k], 10);
    d[k] = isNaN(n) ? null : n;
  }
  d.deadline = normalizeDate(d.deadline);
  return d;
}

// 插入一条实习（含标签关联），返回新 id
async function insertInternship(posterId, d) {
  const { title, company, city, district, job_type, salary_min, salary_max,
          education, days_per_week, duration_months, target_grade, target_major,
          headcount, deadline, apply_time, description, requirements, contact_info, tags } = d;
  const [result] = await pool.query(
    `INSERT INTO internships (poster_id, title, company, city, district, job_type, salary_min, salary_max,
      education, days_per_week, duration_months, target_grade, target_major,
      headcount, deadline, apply_time, description, requirements, contact_info)
     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
    [posterId, title, company, city, district || null, job_type,
     salary_min || null, salary_max || null,
     education || '本科及以上', days_per_week || 4, duration_months || 3,
     target_grade || null, target_major || null,
     headcount || 1, deadline || null, apply_time || null, description || null, requirements || null,
     contact_info || null]
  );
  if (tags && tags.length) {
    for (const tag of tags) {
      try {
        if (typeof tag === 'string' && tag.trim()) {
          const name = tag.trim();
          await pool.query('INSERT IGNORE INTO tags (name) VALUES (?)', [name]);
          const [[t]] = await pool.query('SELECT id FROM tags WHERE name = ?', [name]);
          if (t) await pool.query('INSERT IGNORE INTO internship_tags VALUES (?, ?)', [result.insertId, t.id]);
        }
      } catch (_) { /* 跳过单个标签失败 */ }
    }
  }
  return result.insertId;
}

// 登录
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    const [[user]] = await pool.query('SELECT * FROM users WHERE username = ?', [username]);
    if (!user) return res.status(401).json({ error: '用户名或密码错误' });
    const valid = await bcrypt.compare(password, user.password_hash);
    if (!valid) return res.status(401).json({ error: '用户名或密码错误' });
    if (user.role !== 'admin') return res.status(403).json({ error: '无管理员权限' });
    const token = jwt.sign({ id: user.id, username: user.username, role: 'admin' }, JWT_SECRET, { expiresIn: '12h' });
    res.json({ token, admin: { id: user.id, username: user.username } });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// 仪表盘
router.get('/stats', adminAuth, async (req, res) => {
  try {
    const [[{ total_users }]] = await pool.query('SELECT COUNT(*) AS total_users FROM users');
    const [[{ total_internships }]] = await pool.query('SELECT COUNT(*) AS total_internships FROM internships');
    const [[{ active }]] = await pool.query("SELECT COUNT(*) AS active FROM internships WHERE status='active'");
    const [[{ expired }]] = await pool.query("SELECT COUNT(*) AS expired FROM internships WHERE status='active' AND deadline IS NOT NULL AND deadline < CURDATE()");
    const [[{ today_new }]] = await pool.query('SELECT COUNT(*) AS today_new FROM internships WHERE DATE(created_at) = CURDATE()');
    res.json({ total_users, total_internships, active, expired, today_new });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// 实习列表（含截止日期）
router.get('/internships', adminAuth, async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT i.*, u.username FROM internships i JOIN users u ON i.poster_id = u.id ORDER BY i.created_at DESC LIMIT 200`
    );
    res.json(rows);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// 发布实习
router.post('/internships', adminAuth, async (req, res) => {
  try {
    const { title, company, city, job_type } = req.body;
    if (!title || !company || !city || !job_type) {
      return res.status(400).json({ error: '必填字段：title, company, city, job_type' });
    }
    const id = await insertInternship(req.admin.id, req.body);
    res.status(201).json({ id, message: '发布成功' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 批量导入（csv / xlsx / xls）
router.post('/internships/import', adminAuth, importUpload.single('file'), async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: '请上传 csv 或 excel 文件' });

    const ext = (path.extname(req.file.originalname) || '').toLowerCase();
    let rows;
    if (ext === '.csv') {
      const text = decodeBuffer(req.file.buffer);
      const table = parseCSV(text);
      if (table.length < 2) return res.status(400).json({ error: '文件为空或没有有效数据行' });
      const headers = table[0].map(h => String(h).trim());
      rows = table.slice(1).map(cells => {
        const obj = {};
        headers.forEach((h, i) => { obj[h] = cells[i] !== undefined ? cells[i] : ''; });
        return obj;
      });
    } else {
      const wb = XLSX.read(req.file.buffer, { type: 'buffer', cellDates: true });
      const sheet = wb.Sheets[wb.SheetNames[0]];
      rows = XLSX.utils.sheet_to_json(sheet, { defval: '' });
    }
    if (!rows.length) return res.status(400).json({ error: '文件为空或没有有效数据行' });

    let inserted = 0, skipped = 0;
    const errors = [];
    for (let i = 0; i < rows.length; i++) {
      const d = mapRow(rows[i]);
      if (!d.title || !d.company || !d.city || !d.job_type) {
        skipped++;
        errors.push(`第 ${i + 2} 行：缺少必填字段（岗位名称/公司名称/工作城市/岗位类型）`);
        continue;
      }
      try {
        await insertInternship(req.admin.id, d);
        inserted++;
      } catch (e) {
        skipped++;
        errors.push(`第 ${i + 2} 行：${e.message}`);
      }
    }

    res.json({ inserted, skipped, total: rows.length, errors: errors.slice(0, 20) });
  } catch (err) {
    res.status(400).json({ error: '解析失败：' + err.message });
  }
});

// 批量关闭已截止
router.post('/internships/close-expired', adminAuth, async (req, res) => {
  try {
    const [result] = await pool.query(
      "UPDATE internships SET status = 'closed' WHERE status = 'active' AND deadline IS NOT NULL AND deadline < CURDATE()"
    );
    res.json({ message: `已关闭 ${result.affectedRows} 条已截止实习` });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// 编辑实习
router.put('/internships/:id', adminAuth, async (req, res) => {
  try {
    const { title, company, city, job_type, status, deadline, description, contact_info } = req.body;
    await pool.query(
      `UPDATE internships SET title=?, company=?, city=?, job_type=?, status=?, deadline=?, description=?, contact_info=? WHERE id=?`,
      [title, company, city, job_type, status, deadline || null, description || null, contact_info || null, req.params.id]
    );
    res.json({ message: '更新成功' });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// 删除
router.delete('/internships/:id', adminAuth, async (req, res) => {
  try {
    await pool.query('DELETE FROM internships WHERE id = ?', [req.params.id]);
    res.json({ message: '已删除' });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// 用户列表
router.get('/users', adminAuth, async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT u.id, u.username, u.school, u.role, u.created_at,
        (SELECT COUNT(*) FROM internships WHERE poster_id = u.id) AS share_count
       FROM users u ORDER BY u.created_at DESC`
    );
    res.json(rows);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// 反馈/举报列表
router.get('/reports', adminAuth, async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT r.id, r.user_id, r.internship_id, r.type, r.message, r.status, r.created_at,
              u.username AS reporter, i.title, i.company
       FROM reports r
       LEFT JOIN users u ON r.user_id = u.id
       LEFT JOIN internships i ON r.internship_id = i.id
       ORDER BY r.created_at DESC LIMIT 500`
    );
    res.json(rows);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// 标记反馈为已处理
router.put('/reports/:id', adminAuth, async (req, res) => {
  try {
    await pool.query("UPDATE reports SET status = 'resolved', updated_at = NOW() WHERE id = ?", [req.params.id]);
    res.json({ message: '已标记为已处理' });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// 删除反馈
router.delete('/reports/:id', adminAuth, async (req, res) => {
  try {
    await pool.query('DELETE FROM reports WHERE id = ?', [req.params.id]);
    res.json({ message: '已删除' });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

module.exports = router;
