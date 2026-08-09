/**
 * 爬虫调度 — 抓取最新实习数据并入库
 *
 * 用法：
 *   node maintenance/fetch.js              # 完整流程：抓取→解析→入库
 *   node maintenance/fetch.js --scrape     # 仅抓取
 *   node maintenance/fetch.js --parse      # 仅解析
 *   node maintenance/fetch.js --insert     # 仅入库
 *
 * AI 提示词示例：
 *   "运行 maintenance/fetch.js，抓取最新的实习信息并入库"
 */

const { execSync } = require('child_process');
const path = require('path');

const SCRAPER_DIR = path.join(__dirname, '..', 'server', 'scrapers');
const PYTHON = 'python'; // 或 'python3'

function run(cmd, label) {
  console.log(`\n▶ ${label}...`);
  try {
    const out = execSync(cmd, { cwd: SCRAPER_DIR, encoding: 'utf-8', timeout: 300000 });
    console.log(out.slice(-500));
    return true;
  } catch (e) {
    console.error(`✖ ${label} 失败:`, e.message.slice(0, 200));
    return false;
  }
}

async function main() {
  const args = process.argv.slice(2);
  const mode = args[0] || '';

  console.log('═════════════════════════════════');
  console.log('  实习通 · 数据抓取');
  console.log('═════════════════════════════════');

  switch (mode) {
    case '--scrape':
      run(`${PYTHON} main.py fetch`, '抓取');
      break;
    case '--parse':
      run(`${PYTHON} main.py parse`, '解析');
      break;
    case '--insert':
      run(`${PYTHON} main.py insert`, '入库');
      break;
    default:
      // 全流程
      if (run(`${PYTHON} main.py fetch`, '1/3 抓取')) {
        if (run(`${PYTHON} main.py parse`, '2/3 解析')) {
          run(`${PYTHON} main.py insert`, '3/3 入库');
        }
      }
  }

  console.log('\n✅ 完成');
  process.exit(0);
}

main();
