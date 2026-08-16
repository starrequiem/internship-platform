"""
腾讯校招 — 拦截 searchPosition API 响应，提取岗位列表入库

用法: python scrape_tencent.py
"""
import json
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from playwright.sync_api import sync_playwright
from inserter import insert_item, get_conn

SOURCE_URL = 'https://join.qq.com/post.html'
# 腾讯职位族 -> 岗位类型
FAMILY_MAP = {
    1: '技术开发', 2: '技术开发', 3: '产品经理', 4: 'UI/UX 设计',
    5: '金融投资', 6: '市场商务', 7: '运营', 8: '人力资源', 9: '职能',
}


def scrape():
    items = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})
        captured = {}

        def on_response(resp):
            if 'searchPosition' in resp.url:
                try:
                    data = json.loads(resp.text())
                    if data.get('status') == 0:
                        captured['list'] = data['data'].get('positionList', [])
                except Exception:
                    pass

        page.on('response', on_response)
        try:
            page.goto(SOURCE_URL, wait_until='networkidle', timeout=40000)
            page.wait_for_timeout(4000)
            for _ in range(4):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1200)
        except Exception as e:
            print(f'加载异常: {str(e)[:60]}')
        browser.close()

        plist = captured.get('list', [])
        for pos in plist:
            title = pos.get('positionTitle', '')
            cities = (pos.get('workCities') or '').strip()
            city = cities.split()[0] if cities else '全国'
            fam = pos.get('positionFamily') or 2
            job_type = FAMILY_MAP.get(fam, '技术开发')
            project = pos.get('projectName') or pos.get('recruitLabelName') or ''
            items.append({
                'title': title,
                'company': '腾讯',
                'city': city,
                'job_type': job_type,
                'description': f'招聘项目：{project}\n工作城市：{cities}',
                'requirements': '',
                'contact_info': '🔗 原文链接：' + SOURCE_URL,
                'education': '本科及以上',
                'days_per_week': 4,
                'duration_months': 3,
                'tags': ['腾讯', '大厂'],
            })
    return items


def main():
    items = scrape()
    print(f'提取 {len(items)} 条腾讯岗位')
    for it in items[:8]:
        print(f'  {it["title"][:30]} | {it["city"]} | {it["job_type"]}')

    conn = get_conn()
    ins = skip = 0
    for it in items:
        try:
            if insert_item(it):
                ins += 1
            else:
                skip += 1
        except Exception as e:
            print(f'  ✖ {it["title"][:20]}: {e}')
            skip += 1
    print(f'\n入库: 新增 {ins} | 跳过 {skip}')


if __name__ == '__main__':
    main()
