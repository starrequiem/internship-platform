/**
 * 网站维护脚本 — 一键下架已截止实习
 *
 * 用法（在项目根目录执行）：
 *   node maintenance/cleanup.js          # 预览已截止未下架的
 *   node maintenance/cleanup.js --do     # 执行关闭
 *   node maintenance/cleanup.js --stats  # 统计当前状态
 */

const serverDir = require('path').join(__dirname, '..', 'server');

// 从 server 目录加载模块（node_modules 在 server 里）
const mysql = require(require('path').join(serverDir, 'node_modules', 'mysql2', 'promise'));
require(require('path').join(serverDir, 'node_modules', 'dotenv')).config({ path: require('path').join(serverDir, '.env') });

const pool = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '200619',
  database: process.env.DB_NAME || 'internship_platform',
  charset: 'utf8mb4',
});

async function main() {
  const args = process.argv.slice(2);
  const mode = args[0] || '';

  if (mode === '--stats') await showStats();
  else if (mode === '--do') await closeExpired();
  else await previewExpired();

  await pool.end();
  process.exit(0);
}

async function showStats() {
  const [[{ total }]] = await pool.query("SELECT COUNT(*) AS total FROM internships WHERE status = 'active'");
  const [[{ expired }]] = await pool.query("SELECT COUNT(*) AS expired FROM internships WHERE status = 'active' AND deadline IS NOT NULL AND deadline < CURDATE()");
  const [[{ noDeadline }]] = await pool.query("SELECT COUNT(*) AS noDeadline FROM internships WHERE status = 'active' AND deadline IS NULL");
  console.log('\n═════════════════════════════════');
  console.log('  实习通 · 网站状态');
  console.log('═════════════════════════════════');
  console.log(`  活跃实习：${total} 条`);
  console.log(`  已截止未下架：${expired} 条 ${expired > 0 ? '⚠️' : '✅'}`);
  console.log(`  无截止日期：${noDeadline} 条`);
  console.log('═════════════════════════════════\n');
}

async function previewExpired() {
  const [rows] = await pool.query(
    `SELECT id, title, company, deadline, DATEDIFF(CURDATE(), deadline) AS days_past
     FROM internships WHERE status = 'active' AND deadline IS NOT NULL AND deadline < CURDATE()
     ORDER BY deadline ASC`
  );
  if (!rows.length) { console.log('✅ 没有已截止的实习\n'); return; }
  console.log(`\n⚠️  发现 ${rows.length} 条已截止:\n`);
  for (const r of rows) {
    console.log(`  #${r.id} | ${r.deadline.toISOString().slice(0,10)} | +${r.days_past}天 | ${r.company?.slice(0,12) || '?'} | ${r.title?.slice(0,25) || '?'}`);
  }
  console.log(`\n💡 执行 "node maintenance/cleanup.js --do" 一键关闭\n`);
}

async function closeExpired() {
  const [rows] = await pool.query(
    `SELECT id FROM internships WHERE status = 'active' AND deadline IS NOT NULL AND deadline < CURDATE()`
  );
  if (!rows.length) { console.log('✅ 无需下架\n'); return; }
  const ids = rows.map(r => r.id);
  await pool.query(`UPDATE internships SET status = 'closed' WHERE id IN (?)`, [ids]);
  console.log(`\n✅ 已关闭 ${ids.length} 条: ${ids.join(', ')}\n`);
}

main().catch(e => { console.error('错误:', e.message); process.exit(1); });
