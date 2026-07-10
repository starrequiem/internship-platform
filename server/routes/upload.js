/**
 * 文件上传 API（头像、公司Logo）
 */
const router = require('express').Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { requireAuth } = require('../middleware/auth');

const UPLOAD_DIR = path.join(__dirname, '..', 'uploads');

// 确保目录存在
['avatars', 'logos'].forEach(dir => {
  const p = path.join(UPLOAD_DIR, dir);
  if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true });
});

const storage = multer.diskStorage({
  destination(req, file, cb) {
    const type = req.params.type === 'logo' ? 'logos' : 'avatars';
    cb(null, path.join(UPLOAD_DIR, type));
  },
  filename(req, file, cb) {
    const ext = path.extname(file.originalname) || '.png';
    const name = Date.now() + '-' + Math.round(Math.random() * 1e9) + ext;
    cb(null, name);
  }
});

const upload = multer({
  storage,
  limits: { fileSize: 5 * 1024 * 1024 }, // 5MB
  fileFilter(req, file, cb) {
    const allowed = /\.(jpg|jpeg|png|gif|webp)$/i;
    if (allowed.test(path.extname(file.originalname))) {
      cb(null, true);
    } else {
      cb(new Error('仅支持 jpg/png/gif/webp 格式'));
    }
  }
});

// POST /api/upload/:type  (type = avatar | logo)
router.post('/:type', requireAuth, (req, res) => {
  upload.single('file')(req, res, async (err) => {
    if (err) {
      if (err instanceof multer.MulterError && err.code === 'LIMIT_FILE_SIZE') {
        return res.status(400).json({ error: '文件大小不能超过 5MB' });
      }
      return res.status(400).json({ error: err.message });
    }
    if (!req.file) {
      return res.status(400).json({ error: '请选择文件' });
    }

    const type = req.params.type === 'logo' ? 'logos' : 'avatars';
    const url = `/uploads/${type}/${req.file.filename}`;

    // 如果是头像上传，更新用户表
    if (req.params.type === 'avatar') {
      const pool = require('../db');
      await pool.query('UPDATE users SET avatar_url = ? WHERE id = ?', [url, req.user.id]);
    }

    res.json({ url, message: '上传成功' });
  });
});

module.exports = router;
