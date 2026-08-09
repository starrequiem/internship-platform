"""
完整爬虫 — 列表页收集链接 → 详情页提取完整数据 → 入库
用法: python scraper.py
"""
import json, os, sys, io, re, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from playwright.sync_api import sync_playwright
from inserter import insert_item, get_conn

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'full_jobs')
os.makedirs(OUT_DIR, exist_ok=True)

CITIES = ['北京','上海','广州','深圳','杭州','成都','南京','武汉','西安','苏州']

def collect_listing_urls(page, city=''):
    """从牛客网列表页收集所有岗位URL"""
    url = 'https://www.nowcoder.com/jobs/intern/center?recruitType=2'
    if city: url += '&city=' + city
    print(f'  📋 列表: {city or "全国"}')

    page.goto(url, wait_until='networkidle', timeout=60000)
    for i in range(5):
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        page.wait_for_timeout(1500)

    jobs = page.evaluate('''() => {
        const jobs = [], seen = new Set();
        document.querySelectorAll('a[href*="/jobs/detail/"]').forEach(a => {
            const href = a.getAttribute('href');
            if (href && !seen.has(href)) {
                seen.add(href);
                jobs.push({
                    url: href.startsWith('http') ? href : 'https://www.nowcoder.com' + href,
                    text: (a.innerText || '').trim()
                });
            }
        });
        return jobs;
    }''')
    print(f'    收集 {len(jobs)} 个链接')
    return jobs


def scrape_detail(page, job):
    """抓取岗位详情页，提取完整信息"""
    url = job['url']
    result = {
        'title': '', 'company': '', 'city': '', 'job_type': '技术开发',
        'salary_min': None, 'salary_max': None, 'education': '本科及以上',
        'days_per_week': 4, 'duration_months': 3, 'headcount': 1,
        'deadline': None, 'description': '', 'requirements': '', 'tags': [],
        'contact_info': '', 'url': url,
    }

    try:
        page.goto(url, wait_until='domcontentloaded', timeout=20000)
        page.wait_for_timeout(2000)

        data = page.evaluate('''() => {
            const body = document.body ? document.body.innerText : '';

            // 提取标题
            let title = '';
            const h1 = document.querySelector('h1, .job-title, .position-title');
            if (h1) title = h1.innerText.trim();

            // 提取公司名
            let company = '';
            const cEl = document.querySelector('.company-name, .corp-name, [class*="company-name"]');
            if (cEl) company = cEl.innerText.trim().split('\\n')[0];

            // 搜索描述文本
            let desc = '', req = '';
            const lines = body.split('\\n');
            let inDesc = false, inReq = false;
            for (const line of lines) {
                const l = line.trim();
                if (!l) continue;
                if (l.includes('职位描述') || l.includes('岗位职责') || l.includes('工作内容')) { inDesc = true; inReq = false; continue; }
                if (l.includes('任职要求') || l.includes('岗位要求') || l.includes('职位要求') || l.includes('加分项')) { inReq = true; inDesc = false; continue; }
                if (l.includes('公司介绍') || l.includes('工作地址') || l.includes('投递方式') || l.includes('职位base')) { inDesc = false; inReq = false; continue; }
                if (inDesc) desc += l + '\\n';
                if (inReq) req += l + '\\n';
            }
            if (!desc) desc = body;

            // 标签
            let tags = [];
            document.querySelectorAll('.tag-item, .skill-tag, [class*="tag"] span, .label-item, .tech-tag').forEach(t => {
                const txt = t.innerText.trim();
                if (txt && txt.length < 20 && !tags.includes(txt)) tags.push(txt);
            });

            return {title, company, desc: desc.trim(), req: req.trim(), tags, body};
        }''')

        # 填充结果
        listing_text = job.get('text', '')

        # 从列表文本提取薪资/城市/天数
        sal_match = re.search(r'(\d+)\s*[-~至]\s*(\d+)\s*元/[天日]', listing_text)
        if sal_match:
            result['salary_min'] = int(sal_match.group(1))
            result['salary_max'] = int(sal_match.group(2))

        for c in CITIES:
            if c in listing_text:
                result['city'] = c
                break

        dm = re.search(r'(\d+)\s*天/周', listing_text)
        if dm: result['days_per_week'] = int(dm.group(1))

        durm = re.search(r'最少\s*(\d+)\s*个?月', listing_text)
        if durm: result['duration_months'] = int(durm.group(1))

        # 标题
        title = data.get('title', '') or listing_text.split('\n')[0].strip()
        result['title'] = title[:200]

        # 公司
        result['company'] = data.get('company', '') or '待识别'

        # 描述 — 优先用详情页提取的，否则用列表文本
        desc = data.get('desc', '')
        if not desc or len(desc) < 50:
            desc = listing_text
        result['description'] = desc[:5000]

        # 要求
        result['requirements'] = data.get('req', '')[:3000]

        # 标签
        result['tags'] = data.get('tags', [])[:8]

        # 分类
        title_lower = title.lower()
        if any(k in title_lower for k in ['产品经理','产品','pm']): result['job_type'] = '产品经理'
        elif any(k in title_lower for k in ['运营','主播']): result['job_type'] = '运营'
        elif any(k in title_lower for k in ['设计','ui','ux','管培']): result['job_type'] = 'UI/UX 设计'
        elif any(k in title_lower for k in ['数据','分析']): result['job_type'] = '数据分析'

        # 联系信息
        result['contact_info'] = '🔗 牛客网投递链接：' + url

        # 打印摘要
        desc_len = len(result['description'])
        req_len = len(result['requirements'])
        tags_n = len(result['tags'])
        print(f'    ✅ {result["title"][:30]} | {result["company"][:15]} | desc:{desc_len} req:{req_len} tags:{tags_n}')

    except Exception as e:
        print(f'    ❌ Error: {e}')
        result['description'] = job.get('text', '')[:2000]
        result['contact_info'] = '🔗 牛客网投递链接：' + url

    return result


def main():
    all_jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})

        # 第1步：收集列表页链接
        print('\n═══ 第1步：收集列表页链接 ═══')
        for city in ['', '北京', '上海', '深圳', '广州', '杭州', '成都']:
            jobs = collect_listing_urls(page, city)
            for j in jobs:
                if j['url'] not in [x['url'] for x in all_jobs]:
                    all_jobs.append(j)
            time.sleep(2)

        print(f'\n总计 {len(all_jobs)} 个唯一链接')

        # 第2步：逐条抓取详情
        print(f'\n═══ 第2步：抓取详情页 ═══')
        results = []
        limit = min(len(all_jobs), 40)  # 限制每次40条
        for i, job in enumerate(all_jobs[:limit]):
            print(f'[{i+1}/{limit}]', end=' ')
            result = scrape_detail(page, job)
            results.append(result)
            time.sleep(1.5)

        browser.close()

    # 第3步：入库
    print(f'\n═══ 第3步：入库 ═══')
    inserted = 0
    for item in results:
        try:
            rid = insert_item(item)
            if rid: inserted += 1
        except Exception as e:
            print(f'  Error inserting {item.get("title","?")}: {e}')

    print(f'\n入库: {inserted}/{len(results)}')

    # 保存
    fname = os.path.join(OUT_DIR, f'jobs_{int(time.time())}.json')
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump({'items': results, 'count': len(results)}, f, ensure_ascii=False, indent=2)
    print(f'数据已保存: {fname}')


if __name__ == '__main__':
    main()
