/**
 * 岗位去重 — 删除完全重复岗位（同 title+company+city），保留描述最完整的一条
 * 用法: node maintenance/dedup.js [--do]   (无 --do 只预览)
 */
const path = require('path');
const serverDir = path.join(__dirname, '..', 'server');
const mysql = require(path.join(serverDir, 'node_modules', 'mysql2', 'promise'));
const { db } = require(path.join(serverDir, 'config'));

const pool = mysql.createPool({
  ...db, charset: 'utf8mb4',
});

async function main() {
  const doIt = process.argv.includes('--do');

  const [groups] = await pool.query(
    `SELECT title, company, city, COUNT(*) n, MIN(id) min_id, MAX(id) max_id
     FROM internships GROUP BY title, company, city HAVING n > 1 ORDER BY n DESC`
  );
  console.log(`完全重复组: ${groups.length} 组，涉及多余 ${groups.reduce((s, g) => s + g.n - 1, 0)} 条\n`);

  let totalDeleted = 0;
  for (const g of groups) {
    const [rows] = await pool.query(
      `SELECT id, LENGTH(description) dl, LENGTH(requirements) rl
       FROM internships WHERE title=? AND company=? AND city=? ORDER BY (dl+rl) DESC, id ASC`,
      [g.title, g.company, g.city]
    );
    const keep = rows[0].id;
    const delIds = rows.slice(1).map(r => r.id);
    if (!doIt) {
      console.log(`  ${g.n}x [${g.company}] ${(g.title || '').slice(0, 25)} ${g.city} → 保留#${keep}, 删${delIds.length}条`);
    } else if (delIds.length) {
      await pool.query('DELETE FROM internships WHERE id IN (?)', [delIds]);
      totalDeleted += delIds.length;
    }
  }

  if (doIt) {
    console.log(`\n✅ 已删除 ${totalDeleted} 条重复岗位`);
    const [[{ total }]] = await pool.query('SELECT COUNT(*) total FROM internships');
    console.log(`当前总岗位: ${total}`);
  } else {
    console.log(`\n💡 执行 "node maintenance/dedup.js --do" 真正删除`);
  }
  await pool.end();
  process.exit(0);
}

main().catch(e => { console.error('错误:', e.message); process.exit(1); });
