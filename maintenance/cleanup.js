/**
 * 网站维护脚本 — 一键下架已截止实习
 *
 * 用法：
 *   node maintenance/cleanup.js          # 预览：列出已截止但未下架的
 *   node maintenance/cleanup.js --do     # 执行：关闭所有已截止且未下架的
 *   node maintenance/cleanup.js --stats  # 统计：显示当前状态
 *
 * AI 提示词示例（任何 AI 可调用）：
 *   "用 Node.js 运行 maintenance/cleanup.js --do，关闭所有已截止的实习信息"
 */

const mysql = require('mysql2/promise');
require('dotenv').config({ path: require('path').join(__dirname, '..', 'server', '.env') });

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

  if (mode === '--stats') {
    await showStats();
  } else if (mode === '--do') {
    await closeExpired();
  } else {
    await previewExpired();
  }
  process.exit(0);
}

async function showStats() {
  const [[{ total }]] = await pool.query(
    "SELECT COUNT(*) AS total FROM internships WHERE status = 'active'"
  );
  const [[{ expired }]] = await pool.query(
    "SELECT COUNT(*) AS expired FROM internships WHERE status = 'active' AND deadline IS NOT NULL AND deadline < CURDATE()"
  );
  const [[{ noDeadline }]] = await pool.query(
    "SELECT COUNT(*) AS noDeadline FROM internships WHERE status = 'active' AND deadline IS NULL"
  );
  console.log('═════════════════════════════════');
  console.log('  实习通 · 网站状态');
  console.log('═════════════════════════════════');
  console.log(`  活跃实习：${total} 条`);
  console.log(`  已截止未下架：${expired} 条 ⚠️`);
  console.log(`  无截止日期：${noDeadline} 条`);
  console.log('═════════════════════════════════');
}

async function previewExpired() {
  const [rows] = await pool.query(
    `SELECT id, title, company, city, deadline, DATEDIFF(CURDATE(), deadline) AS days_past,
            view_count, favorite_count
     FROM internships
     WHERE status = 'active' AND deadline IS NOT NULL AND deadline < CURDATE()
     ORDER BY deadline ASC`
  );

  if (!rows.length) {
    console.log('✅ 没有已截止的实习，网站状态良好！');
    return;
  }

  console.log(`⚠️  发现 ${rows.length} 条已截止的实习（预览模式，未执行）：\n`);
  console.log('ID    | 截止日期   | 过期天数 | 公司        | 岗位');
  console.log('------|-----------|---------|------------|------------------');
  for (const r of rows) {
    console.log(`#${String(r.id).padEnd(4)} | ${r.deadline.toISOString().slice(0,10)} | ${String(r.days_past).padEnd(7)} | ${(r.company||'').slice(0,10).padEnd(10)} | ${(r.title||'').slice(0,20)}`);
  }
  console.log(`\n💡 执行 "node maintenance/cleanup.js --do" 来一键关闭这 ${rows.length} 条`);
}

async function closeExpired() {
  const [rows] = await pool.query(
    `SELECT id FROM internships
     WHERE status = 'active' AND deadline IS NOT NULL AND deadline < CURDATE()`
  );

  if (!rows.length) {
    console.log('✅ 没有需要下架的实习');
    return;
  }

  const ids = rows.map(r => r.id);
  await pool.query(
    `UPDATE internships SET status = 'closed' WHERE id IN (?)`,
    [ids]
  );
  console.log(`✅ 已下架 ${ids.length} 条已截止实习`);
  console.log(`   关闭的ID: ${ids.join(', ')}`);
}

main().catch(e => { console.error('错误:', e.message); process.exit(1); });
