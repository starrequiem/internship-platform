"""
腾讯校招 — 直连 searchPosition API 分页抓全
参考: github.com/HA7CH/job-pro (tencent.ts)

POST /api/v1/position/searchPosition  body 含 pageIndex/pageSize
用法: python scrape_tencent.py [--max-pages 20] [--with-detail]
"""
import json
import os
import sys
import io
import argparse
import time
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from inserter import insert_item, get_conn

API = 'https://join.qq.com/api/v1/position/searchPosition'
DETAIL = 'https://join.qq.com/api/v1/jobDetails/getJobDetailsByPostId?postId={}'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://join.qq.com/post.html',
    'Content-Type': 'application/json',
}

FAMILY_MAP = {1: '技术开发', 2: '技术开发', 3: '产品经理', 4: 'UI/UX 设计',
              5: '金融投资', 6: '市场商务', 7: '运营', 8: '人力资源', 9: '职能支持'}


def search_page(page_index, page_size=100):
    body = {
        'projectIdList': [], 'projectMappingIdList': [], 'keyword': '',
        'bgList': [], 'workCountryType': 0, 'workCityList': [],
        'recruitCityList': [], 'positionFidList': [],
        'pageIndex': page_index, 'pageSize': page_size,
    }
    r = requests.post(API, json=body, headers=HEADERS, timeout=30)
    d = r.json()
    return d.get('data', {}) if d.get('status') == 0 else {}


def fetch_detail(post_id):
    try:
        r = requests.get(DETAIL.format(post_id), headers=HEADERS, timeout=20)
        d = r.json()
        return d.get('data', {}) if d.get('status') == 0 else {}
    except Exception:
        return {}


def fetch_jobs(max_pages=15, page_size=100, with_detail=False):
    items = []
    for page in range(1, max_pages + 1):
        data = search_page(page, page_size)
        lst = data.get('positionList', [])
        if not lst:
            break
        for p in lst:
            cities = (p.get('workCities') or '').strip()
            city = cities.split()[0] if cities else '全国'
            fam = p.get('positionFamily') or 2
            job_type = FAMILY_MAP.get(fam, '技术开发')
            project = p.get('projectName') or p.get('recruitLabelName') or ''
            desc = f'招聘项目：{project}\n工作城市：{cities}'
            if with_detail:
                d = fetch_detail(p.get('postId', ''))
                if d.get('jobDuty') or d.get('jobRequire'):
                    desc = (d.get('jobDuty') or '')[:5000]
                    req = (d.get('jobRequire') or '')[:3000]
                else:
                    req = ''
                time.sleep(0.15)
            else:
                req = ''
            items.append({
                'title': p.get('positionTitle', ''),
                'company': '腾讯',
                'city': city,
                'job_type': job_type,
                'description': desc,
                'requirements': req,
                'contact_info': '🔗 原文链接：https://join.qq.com/post.html',
                'education': '本科及以上',
                'days_per_week': 4, 'duration_months': 3,
                'tags': ['腾讯', '大厂'],
            })
        print(f'  page {page}: 累计 {len(items)} 条')
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--max-pages', type=int, default=15)
    ap.add_argument('--with-detail', action='store_true')
    args = ap.parse_args()
    items = fetch_jobs(args.max_pages, with_detail=args.with_detail)
    print(f'\n提取 {len(items)} 条腾讯岗位')
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
        except Exception:
            skip += 1
    print(f'\n入库: 新增 {ins} | 跳过 {skip}')


if __name__ == '__main__':
    main()
