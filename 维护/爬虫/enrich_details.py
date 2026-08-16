"""
批量丰富详情数据 — 访问每个岗位URL，提取完整描述并更新数据库
"""
import json, os, sys, io, re, glob, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from playwright.sync_api import sync_playwright
from inserter import get_conn
from config import extract_company_fallback
from extract import split_detail

def scrape_one(page, url):
    """抓取单个详情页，返回 {desc, req, company, tags}（按标题边界稳健分割）"""
    result = {'desc': '', 'req': '', 'company': '', 'tags': []}
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=25000)
        page.wait_for_timeout(2500)
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        page.wait_for_timeout(800)

        body = page.evaluate('() => document.body ? document.body.innerText : ""') or ''
        desc, req = split_detail(body)
        result['desc'] = desc[:5000]
        result['req'] = req[:3000]

        company = page.evaluate('''() => {
            const el = document.querySelector('.company-name, .corp-name, [class*="company-name"]');
            return el ? el.innerText.trim().split('\\n')[0] : '';
        }''')
        result['company'] = company or extract_company_fallback(body)

        result['tags'] = page.evaluate('''() => {
            const t = [];
            document.querySelectorAll('.tag-item, .skill-tag, [class*="tag"] span, .label-item, .tech-tag').forEach(el => {
                const txt = el.innerText.trim();
                if (txt && txt.length < 20 && t.indexOf(txt) < 0) t.push(txt);
            });
            return t.slice(0, 10);
        }''')

    except Exception as e:
        print(f'  Error: {e}')
    return result

def main():
    conn = get_conn()
    cur = conn.cursor()

    # 获取所有有牛客详情URL、但任职要求为空或描述过短的实习
    cur.execute("""
        SELECT id, contact_info FROM internships
        WHERE contact_info LIKE '%nowcoder.com/jobs/detail/%'
        AND (requirements IS NULL OR requirements = '' OR LENGTH(description) < 100)
        ORDER BY id
    """)
    rows = cur.fetchall()
    print(f'需要丰富: {len(rows)} 条')

    if not rows:
        print('全部已有足够描述，无需更新')
        conn.close()
        return

    urls = []
    for row in rows:
        m = re.search(r'(https://www\.nowcoder\.com/jobs/detail/\d+)', row[1] or '')
        if m:
            urls.append((row[0], m.group(1)))

    print(f'有效URL: {len(urls)} 条')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})

        updated = 0
        for i, (tid, url) in enumerate(urls):
            print(f'[{i+1}/{len(urls)}] #{tid} {url[:70]}')
            data = scrape_one(page, url)

            # 更新数据库
            desc = data['desc']
            req = data['req']
            company = data['company']
            tags = ','.join(data['tags'][:8])

            if desc or req or company or tags:
                parts = []
                vals = []
                if desc and len(desc) > 50:
                    parts.append('description = %s'); vals.append(desc[:5000])
                if req and len(req) > 20:
                    parts.append('requirements = %s'); vals.append(req[:3000])
                if company and len(company) > 2 and company != '待识别':
                    parts.append('company = %s'); vals.append(company[:100])

                if parts:
                    vals.append(tid)
                    cur.execute('UPDATE internships SET ' + ', '.join(parts) + ' WHERE id = %s', vals)
                    updated += 1
                    print(f'  Updated: desc={len(desc)} req={len(req)} company={company[:20]}')

            time.sleep(1)

        browser.close()

    conn.commit()
    cur.execute('SELECT COUNT(*) FROM internships WHERE LENGTH(description) < 100 OR description IS NULL')
    remaining = cur.fetchone()[0]
    print(f'\nUpdated: {updated}, Remaining thin: {remaining}')
    conn.close()

if __name__ == '__main__':
    main()
