"""
阿里校招/实习 — 直连 campus-talent.alibaba.com 公开 API
参考: github.com/HA7CH/job-pro (alibaba.ts)

用法: python scrape_alibaba.py [--scope intern|campus|all]
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

ROOT = 'https://campus-talent.alibaba.com'
CHANNEL = 'new_campus_group_official_site'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36'

FAMILY_MAP = {
    '技术类': '技术开发', '产品类': '产品经理', '设计类': 'UI/UX 设计',
    '运营类': '运营', '数据类': '数据分析', '市场类': '市场商务',
    '职能类': '人力资源', '游戏类': '产品经理',
}


class AlibabaClient:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update({'User-Agent': UA})
        self.s.get(ROOT + '/campus/position', timeout=30)
        self.xsrf = self.s.cookies.get('XSRF-TOKEN', '')

    def _post(self, path, body):
        return self.s.post(ROOT + path, json=body, timeout=30,
                           headers={'X-XSRF-TOKEN': self.xsrf, 'Content-Type': 'application/json'}).json()

    def list_batches(self):
        d = self._post('/searchCondition/listBatch', {})
        return d.get('content', {})

    def search(self, batch_id, page_index, page_size=50):
        body = {
            'batchId': batch_id, 'pageIndex': page_index, 'pageSize': page_size,
            'channel': CHANNEL, 'language': 'zh',
        }
        return self._post('/position/search', body)


def fetch_jobs(scope='intern', max_pages=8):
    c = AlibabaClient()
    batches = c.list_batches()
    if scope == 'intern':
        targets = batches.get('internship', [])
    elif scope == 'campus':
        targets = batches.get('graduate', [])
    else:
        targets = batches.get('graduate', []) + batches.get('internship', []) + batches.get('topTalentPlan', [])

    items = []
    for b in targets:
        bid, bname = b['id'], b['name']
        for page_idx in range(1, max_pages + 1):
            d = c.search(bid, page_idx)
            datas = d.get('content', {}).get('datas', []) if d.get('success') else []
            if not datas:
                break
            for it in datas:
                cities = it.get('workLocations') or []
                items.append({
                    'title': it.get('name', ''),
                    'company': '阿里巴巴',
                    'city': cities[0] if cities else '全国',
                    'job_type': FAMILY_MAP.get(it.get('categoryName', ''), '技术开发'),
                    'description': (it.get('description') or '')[:5000],
                    'requirements': (it.get('requirement') or '')[:3000],
                    'contact_info': '🔗 原文链接：' + ROOT + '/campus/position/' + str(it.get('id', '')),
                    'education': '本科及以上',
                    'days_per_week': 4, 'duration_months': 3,
                    'tags': ['阿里巴巴', '大厂', bname],
                })
            total = d.get('content', {}).get('totalCount', 0)
            if page_idx * 50 >= total:
                break
        print(f'  {bname}: {sum(1 for x in items if x["title"])} 条累计')
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scope', default='intern', choices=['intern', 'campus', 'all'])
    args = ap.parse_args()
    items = fetch_jobs(args.scope)
    print(f'\n提取 {len(items)} 条阿里岗位')
    for it in items[:8]:
        print(f'  {it["title"][:30]} | {it["city"]} | {it["job_type"]} | desc:{len(it["description"])}')

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
