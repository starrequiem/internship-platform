const mysql = require('mysql2/promise');

const pool = mysql.createPool({
  host: 'localhost',
  user: 'root',
  password: '200619',
  database: 'internship_platform',
  charset: 'utf8mb4',
  charsetNumber: 224, // utf8mb4_unicode_ci, 防止中文乱码
  waitForConnections: true,
  connectionLimit: 10,
});

module.exports = pool;
