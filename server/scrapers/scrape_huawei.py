"""
华为校招 — 点「实习生」筛选后拦截 getJob API，提取岗位入库
用法: python scrape_huawei.py
"""
import json
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from playwright.sync_api import sync_playwright
from config import CITIES
from inserter import insert_item, get_conn

SOURCE_URL = 'https://career.huawei.com/reccampportal/portal5/campus-recruitment.html'


def scrape():
    items = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})
        captured = {}

        def on_response(resp):
            if 'getJob' in resp.url:
                try:
                    d = json.loads(resp.text())
                    if d.get('result'):
                        captured['list'] = d['result']
                except Exception:
                    pass

        page.on('response', on_response)
        try:
            page.goto(SOURCE_URL, wait_until='networkidle', timeout=40000)
            page.wait_for_timeout(4000)
            # 点「实习生」
            page.evaluate('''() => {
                const els = [...document.querySelectorAll('li, div, span, a')];
                const el = els.find(e => e.innerText && e.innerText.trim() === '实习生');
                if (el) el.click();
            }''')
            page.wait_for_timeout(4000)
            for _ in range(4):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1200)
        except Exception as e:
            print(f'加载异常: {str(e)[:60]}')
        browser.close()

        for job in captured.get('list', []):
            title = job.get('jobName') or job.get('positionName') or job.get('jobTitle') or ''
            city = (job.get('workCity') or job.get('city') or job.get('workPlace') or '')
            # 城市字段可能是 '深圳', 也可能是多城市
            city = (city or '').strip()
            items.append({
                'title': title,
                'company': '华为',
                'city': city or '全国',
                'job_type': '技术开发',
                'description': json.dumps(job, ensure_ascii=False)[:2000],
                'requirements': '',
                'contact_info': '🔗 原文链接：' + SOURCE_URL,
                'education': '本科及以上',
                'days_per_week': 4,
                'duration_months': 3,
                'tags': ['华为', '大厂', '实习'],
            })
    return items


def main():
    items = scrape()
    print(f'提取 {len(items)} 条华为岗位')
    for it in items[:10]:
        print(f'  {it["title"][:40]} | {it["city"]}')
    if items:
        conn = get_conn()
        ins = skip = 0
        for it in items:
            try:
                if insert_item(it):
                    ins += 1
                else:
                    skip += 1
            except Exception as e:
                skip += 1
        print(f'\n入库: 新增 {ins} | 跳过 {skip}')


if __name__ == '__main__':
    main()
