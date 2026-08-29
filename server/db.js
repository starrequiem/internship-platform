const mysql = require('mysql2/promise');
const { db } = require('./config');

const pool = mysql.createPool({
  host: db.host,
  port: db.port,
  user: db.user,
  password: db.password,
  database: db.database,
  charset: 'utf8mb4',
  charsetNumber: 224, // utf8mb4_unicode_ci, 防止中文乱码
  waitForConnections: true,
  connectionLimit: 10,
});

module.exports = pool;
