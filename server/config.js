const path = require('path');

require('dotenv').config({ path: process.env.ENV_FILE || path.join(__dirname, '.env') });

const isProduction = process.env.NODE_ENV === 'production';

function secret(name, developmentFallback) {
  const value = process.env[name];
  if (value) return value;
  if (isProduction) {
    throw new Error(`${name} 必须在生产环境中设置`);
  }
  return developmentFallback;
}

const uploadDir = path.resolve(process.env.UPLOAD_DIR || path.join(__dirname, 'uploads'));

module.exports = {
  isProduction,
  port: Number(process.env.PORT) || 3000,
  frontendRoot: path.resolve(__dirname, '..'),
  uploadDir,
  jwtSecret: secret('JWT_SECRET', 'local-user-secret-change-before-production'),
  adminJwtSecret: secret('ADMIN_JWT_SECRET', 'local-admin-secret-change-before-production'),
  corsOrigins: (process.env.CORS_ORIGINS || 'http://localhost:8080,http://127.0.0.1:8080')
    .split(',')
    .map(origin => origin.trim())
    .filter(Boolean),
  db: {
    host: process.env.DB_HOST || process.env.MYSQLHOST || 'localhost',
    port: Number(process.env.DB_PORT || process.env.MYSQLPORT) || 3306,
    user: process.env.DB_USER || process.env.MYSQLUSER || 'root',
    password: process.env.DB_PASSWORD || process.env.MYSQLPASSWORD || '',
    database: process.env.DB_NAME || process.env.MYSQLDATABASE || 'internship_platform',
  },
};
