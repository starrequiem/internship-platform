"""
字节跳动校招/实习 — 浏览器内 fetch 分页抓取（反爬需浏览器会话）
参考: github.com/HA7CH/job-pro (bytedance.ts)

用法: python scrape_bytedance.py [--scope intern|campus|all] [--max 500]
"""
import json
import os
import sys
import io
import argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from playwright.sync_api import sync_playwright
from inserter import insert_item, get_conn

CAMPUS_PAGE = 'https://jobs.bytedance.com/campus/position'
DETAIL = 'https://jobs.bytedance.com/campus/position/{}'

SCOPE_RECRUIT = {'intern': ['202'], 'campus': ['201'], 'all': ['201', '202']}


def classify(category):
    if not category:
        return '技术开发'
    if '算法' in category or 'AI' in category or '机器学习' in category:
        return '算法/AI'
    if '产品' in category:
        return '产品经理'
    if '设计' in category or 'UI' in category or 'UX' in category:
        return 'UI/UX 设计'
    if '运营' in category:
        return '运营'
    if '市场' in category or '销售' in category or '商务' in category:
        return '市场商务'
    if '数据' in category:
        return '数据分析'
    if '人力' in category or 'HR' in category:
        return '人力资源'
    return '技术开发'


def fetch_jobs(scope='intern', max_posts=500, page_size=100):
    recruit_ids = SCOPE_RECRUIT[scope]
    items = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(CAMPUS_PAGE, wait_until='domcontentloaded', timeout=40000)
        page.wait_for_timeout(3000)

        # 字节 API 现已要求 x-csrf-token 头，先获取 token
        token = page.evaluate('''async () => {
            const r = await fetch('https://jobs.bytedance.com/api/v1/csrf/token', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({'portal_entrance':1})
            });
            const j = await r.json();
            return (j && j.data && j.data.token) || '';
        }''')
        if not token:
            print('  获取 CSRF token 失败，字节 API 可能已升级')
            browser.close()
            return items

        for rec_id in recruit_ids:
            offset = 0
            while len(items) < max_posts:
                body = {'keyword': '', 'limit': page_size, 'offset': offset,
                        'job_category_id_list': [], 'tag_id_list': [],
                        'location_code_list': [], 'subject_id_list': [],
                        'recruitment_id_list': [rec_id], 'portal_type': 3,
                        'job_function_id_list': [], 'storefront_id_list': [],
                        'portal_entrance': 1}
                qs = ('keyword=&limit={limit}&offset={offset}&job_category_id_list=&tag_id_list='
                      '&location_code_list=&subject_id_list=&recruitment_id_list={rec}'
                      '&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1'
                      ).format(limit=page_size, offset=offset, rec=rec_id)
                data = page.evaluate('''async (args) => {
                    const r = await fetch('https://jobs.bytedance.com/api/v1/search/job/posts?' + args.qs, {
                        method: 'POST',
                        headers: {'Content-Type':'application/json',
                                  'x-csrf-token': args.token,
                                  'portal-channel':'campus','portal-platform':'pc','website-path':'campus'},
                        body: JSON.stringify(args.body)
                    });
                    const t = await r.text();
                    try { return JSON.parse(t); } catch(e) { return {code:-1, err:t.slice(0,100)}; }
                }''', {'qs': qs, 'token': token, 'body': body})
                if data.get('code') != 0:
                    print(f'  API异常: {data.get("err", data.get("code"))}')
                    break
                lst = data.get('data', {}).get('job_post_list', [])
                if not lst:
                    break
                for j in lst:
                    city_info = j.get('city_info') or {}
                    city = city_info.get('name', '')
                    cat = (j.get('job_category') or {})
                    cat_name = cat.get('name', '') if isinstance(cat, dict) else str(cat or '')
                    items.append({
                        'title': j.get('title', ''),
                        'company': '字节跳动',
                        'city': city or '全国',
                        'job_type': classify(cat_name),
                        'description': (j.get('description') or '')[:5000],
                        'requirements': (j.get('requirement') or '')[:3000],
                        'contact_info': '🔗 原文链接：' + DETAIL.format(j.get('id', '')),
                        'education': '本科及以上',
                        'days_per_week': 4, 'duration_months': 3,
                        'tags': ['字节跳动', '大厂'],
                    })
                total = data.get('data', {}).get('count', 0)
                offset += page_size
                if offset >= total:
                    break
        browser.close()
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scope', default='intern', choices=['intern', 'campus', 'all'])
    ap.add_argument('--max', type=int, default=500)
    args = ap.parse_args()
    items = fetch_jobs(args.scope, args.max)
    print(f'提取 {len(items)} 条字节岗位')
    for it in items[:8]:
        print(f'  {it["title"][:30]} | {it["city"]} | {it["job_type"]} | desc:{len(it["description"])} req:{len(it["requirements"])}')

    conn = get_conn()
    ins = skip = 0
    for it in items:
        try:
            if insert_item(it):
                ins += 1
            else:
                skip += 1
        except Exception:
            skip += 1
    print(f'\n入库: 新增 {ins} | 跳过 {skip}')


if __name__ == '__main__':
    main()
