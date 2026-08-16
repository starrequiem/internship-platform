"""
美团校招/实习 — 直接调公开 API（无需浏览器）
接口: POST /api/official/job/getJobList
参考: github.com/HA7CH/job-pro (meituan.ts)

用法: python scrape_meituan.py [--scope intern|campus|all]
"""
import json
import os
import sys
import io
import argparse
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from inserter import insert_item, get_conn

API = 'https://zhaopin.meituan.com/api/official/job/getJobList'
DETAIL = 'https://zhaopin.meituan.com/web/position/detail?jobUnionId={}&jobShareType=1&highlightType=campus'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://zhaopin.meituan.com/web/campus',
    'Content-Type': 'application/json',
}

FAMILY_MAP = {
    '技术类': '技术开发', '产品类': '产品经理', '设计类': 'UI/UX 设计',
    '运营类': '运营', '商业分析类': '数据分析', '市场营销类': '市场商务',
    '职能类': '人力资源', '销售、客服与支持类': '市场商务', '零售类': '运营',
}


def fetch_jobs(scope='intern', max_pages=6, page_size=100):
    job_type = {'intern': '2', 'campus': '1', 'all': None}[scope]
    items = []
    for page_no in range(1, max_pages + 1):
        body = {
            'page': {'pageNo': page_no, 'pageSize': page_size},
            'jobShareType': '1',
            'jobType': [{'code': job_type, 'subCode': []}] if job_type else [],
            'cityList': [], 'department': [], 'keywords': '',
        }
        r = requests.post(API, json=body, headers=HEADERS, timeout=30)
        d = r.json()
        if d.get('status') != 1:
            break
        lst = d.get('data', {}).get('list', [])
        if not lst:
            break
        for j in lst:
            cities = [c.get('name', '') for c in (j.get('cityList') or [])]
            dept = (j.get('department') or [{}])[0].get('name', '')
            items.append({
                'title': j.get('name', ''),
                'company': '美团',
                'city': cities[0] if cities else '全国',
                'job_type': FAMILY_MAP.get(j.get('jobFamily', ''), '技术开发'),
                'description': (j.get('jobDuty') or j.get('desc') or '')[:5000],
                'requirements': (j.get('jobRequirement') or '')[:3000],
                'contact_info': '🔗 原文链接：' + DETAIL.format(j.get('jobUnionId', '')),
                'education': '本科及以上',
                'days_per_week': 4, 'duration_months': 3,
                'tags': ['美团', '大厂'] + ([j.get('jobFamilyGroup', '')] if j.get('jobFamilyGroup') else []),
            })
        print(f'  page {page_no}: 累计 {len(items)} 条')
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scope', default='intern', choices=['intern', 'campus', 'all'])
    args = ap.parse_args()
    items = fetch_jobs(args.scope)
    print(f'\n提取 {len(items)} 条美团岗位')
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
        except Exception as e:
            skip += 1
    print(f'\n入库: 新增 {ins} | 跳过 {skip}')


if __name__ == '__main__':
    main()
