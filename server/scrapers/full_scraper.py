"""
完整数据爬虫 — 从牛客网列表页提取岗位链接，批量抓取详情页文本
输出: JSON文件，每岗位含完整描述、要求、公司等
"""
import json, os, time, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'full_jobs')
os.makedirs(OUT_DIR, exist_ok=True)

CITIES = ['北京','上海','广州','深圳','杭州','成都','南京','武汉','西安','苏州','远程办公']

def get_nc_list(page, city=''):
    """从牛客网列表页提取所有岗位链接"""
    url = 'https://www.nowcoder.com/jobs/intern/center?recruitType=2'
    if city:
        url += '&city=' + city

    print(f'  Loading list: {city or "全国"}')
    page.goto(url, wait_until='networkidle', timeout=60000)
    page.wait_for_timeout(5000)

    # 多次滚动加载
    for i in range(3):
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        page.wait_for_timeout(2000)

    # 用JS提取所有岗位链接
    jobs = page.evaluate('''() => {
        const jobs = [];
        const seen = new Set();
        document.querySelectorAll('a[href*="/jobs/detail/"]').forEach(a => {
            const href = a.getAttribute('href');
            if (href && !seen.has(href)) {
                seen.add(href);
                const url = href.startsWith('http') ? href : 'https://www.nowcoder.com' + href;
                const text = (a.innerText || '').trim();
                jobs.push({url: url, text: text});
            }
        });
        return jobs;
    }''')
    print(f'  Found {len(jobs)} job links')
    return jobs

def scrape_detail_page(page, job_url):
    """抓取单个详情页的完整文本"""
    try:
        page.goto(job_url, wait_until='networkidle', timeout=30000)
        page.wait_for_timeout(2000)

        # 用JS提取页面正文（避免编码问题）
        data = page.evaluate('''() => {
            const get = (sel) => {
                const el = document.querySelector(sel);
                return el ? el.innerText.trim() : '';
            };
            return {
                title: get('h1') || get('.job-title') || get('[class*="title"]'),
                company: get('.company-name') || get('.corp-name') || get('[class*="company"]'),
                body: document.body.innerText.slice(0, 15000),
                html: document.querySelector('.job-desc, .position-desc, [class*="desc"], article, .job-content')?.innerText || ''
            };
        }''')

        return {
            'url': job_url,
            'title': data.get('title', '')[:200],
            'company': data.get('company', '')[:100],
            'body': data.get('body', '')[:10000],
            'html_desc': data.get('html', '')[:5000],
        }
    except Exception as e:
        return {'url': job_url, 'error': str(e)}


def main():
    all_jobs = []
    cities = ['', '北京', '上海', '深圳']

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})

        # 第1步：收集所有岗位链接
        for city in cities:
            jobs = get_nc_list(page, city)
            for j in jobs:
                if j['url'] not in [x['url'] for x in all_jobs]:
                    all_jobs.append(j)
            time.sleep(2)

        print(f'\n总计 {len(all_jobs)} 个唯一岗位链接')

        # 第2步：抓取每个详情页
        results = []
        for i, job in enumerate(all_jobs[:30]):  # 先抓30个
            print(f'[{i+1}/{min(30,len(all_jobs))}] {job["url"][:70]}')
            detail = scrape_detail_page(page, job['url'])
            detail['list_text'] = job.get('text', '')
            results.append(detail)
            time.sleep(1)

        browser.close()

    # 保存
    fname = os.path.join(OUT_DIR, f'full_jobs_{int(time.time())}.json')
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump({'items': results, 'count': len(results)}, f, ensure_ascii=False, indent=2)
    print(f'\nSaved {len(results)} jobs to {fname}')


if __name__ == '__main__':
    main()
