const fs = require('fs');
const path = require('path');
const mysql = require('mysql2/promise');
const bcrypt = require('bcryptjs');
const { db } = require('../config');

async function main() {
  const connection = await mysql.createConnection({ ...db, multipleStatements: true });
  try {
    const schemaPath = path.join(__dirname, '..', '..', 'sql', 'production-schema.sql');
    const schema = fs.readFileSync(schemaPath, 'utf8');
    await connection.query(schema);

    const username = process.env.ADMIN_USERNAME;
    const password = process.env.ADMIN_PASSWORD;
    if (username && password) {
      if (password.length < 12) {
        throw new Error('ADMIN_PASSWORD 至少需要 12 个字符');
      }
      const [existing] = await connection.query(
        'SELECT id, role FROM users WHERE username = ?',
        [username]
      );
      if (!existing.length) {
        const hash = await bcrypt.hash(password, 12);
        await connection.query(
          "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
          [username, hash]
        );
        console.log(`数据库结构已就绪；管理员 ${username} 已创建`);
      } else if (existing[0].role !== 'admin') {
        throw new Error(`ADMIN_USERNAME ${username} 已被非管理员用户占用`);
      } else {
        console.log(`数据库结构已就绪；管理员 ${username} 已存在，密码保持不变`);
      }
    } else {
      console.log('数据库结构已就绪；未设置 ADMIN_USERNAME/ADMIN_PASSWORD，跳过管理员创建');
    }
  } finally {
    await connection.end();
  }
}

main().catch(err => {
  console.error('数据库初始化失败:', err.message);
  process.exit(1);
});
