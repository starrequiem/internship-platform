"""
小红书校招/实习 — 直连 job.xiaohongshu.com 公开 API（SPA宿主免鉴权）
参考: github.com/HA7CH/job-pro (xiaohongshu.ts)

接口: POST /websiterecruit/position/pageQueryPosition
  body: {recruitType:"campus"|"social", positionName?, pageNum, pageSize}

用法: python scrape_xiaohongshu.py [--scope campus|social|all]
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

API = 'https://job.xiaohongshu.com/websiterecruit/position/pageQueryPosition'
DETAIL = 'https://job.xiaohongshu.com/campus/position/{}'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36',
    'Content-Type': 'application/json', 'Accept': 'application/json',
}

TECH_KW = ['大模型', '策略算法', '客户端', '后端', '前端', '多媒体算法', '内容理解', '引擎',
           '数据科学', '机器学习', '基础后端', '运维', '基础安全', '端点防护', '算法', '开发']
PRODUCT_KW = ['产品经理']
DESIGN_KW = ['体验设计', '设计']
OPS_KW = ['运营']
MARKET_KW = ['营销', '行业销售', '经营策略', '销售']
HR_KW = ['招聘']
FUNC_KW = ['法务', '政府事务']


def classify(job_type):
    if any(k in job_type for k in TECH_KW):
        return '技术开发'
    if any(k in job_type for k in PRODUCT_KW):
        return '产品经理'
    if any(k in job_type for k in DESIGN_KW):
        return 'UI/UX 设计'
    if any(k in job_type for k in OPS_KW):
        return '运营'
    if any(k in job_type for k in MARKET_KW):
        return '市场商务'
    if any(k in job_type for k in HR_KW):
        return '人力资源'
    if any(k in job_type for k in FUNC_KW):
        return '职能'
    return '技术开发'


def clean_city(workplace):
    if not workplace:
        return '全国'
    first = workplace.split('，')[0].split(',')[0].strip()
    return first.replace('市', '') if first else '全国'


def fetch_jobs(scope='campus', max_pages=20, page_size=100):
    recruit_types = {'campus': ['campus'], 'social': ['social'], 'all': ['campus', 'social']}[scope]
    items = []
    for rt in recruit_types:
        for page_num in range(1, max_pages + 1):
            body = {'recruitType': rt, 'pageNum': page_num, 'pageSize': page_size}
            r = requests.post(API, json=body, headers=HEADERS, timeout=30)
            d = r.json()
            data = d.get('data') or {}
            lst = data.get('list') or []
            if not lst:
                break
            for j in lst:
                items.append({
                    'title': j.get('positionName', ''),
                    'company': '小红书',
                    'city': clean_city(j.get('workplace', '')),
                    'job_type': classify(j.get('jobType') or ''),
                    'description': (j.get('duty') or '')[:5000],
                    'requirements': (j.get('qualification') or '')[:3000],
                    'contact_info': '🔗 原文链接：' + DETAIL.format(j.get('positionId', '')),
                    'education': '本科及以上',
                    'days_per_week': 4, 'duration_months': 3,
                    'tags': ['小红书', '大厂'] + ([j.get('jobType', '')] if j.get('jobType') else []),
                })
            total = data.get('total', 0)
            if page_num * page_size >= total:
                break
        print(f'  {rt}: 累计 {sum(1 for x in items)} 条')
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scope', default='campus', choices=['campus', 'social', 'all'])
    args = ap.parse_args()
    items = fetch_jobs(args.scope)
    print(f'\n提取 {len(items)} 条小红书岗位')
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
