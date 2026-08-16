"""
华为校招/实习 — 直连 career.huawei.com 公开 API
参考: github.com/HA7CH/job-pro (huawei.ts)

接口: GET getJob/newHr/page/{pageSize}/{curPage}?jobType=...&language=zh_CN
  jobType=3  → 全部校招类型
  jobType=0&jobTypes=2 → 应届生
  jobType=0&jobTypes=0 → 实习生/博士
需先 GET /reccampportal/ 拿 JSESSIONID + 带 Referer 头。

用法: python scrape_huawei.py
"""
import json
import os
import sys
import io
import re
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from inserter import insert_item, get_conn

ROOT = 'https://career.huawei.com/reccampportal'
API = ROOT + '/services/portal/portalpub/getJob/newHr/page/{}/{}'
DETAIL = ROOT + '/portal5/campus-recruitment-detail.html?jobId={}&dataSource={}'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': ROOT + '/portal5/campus-recruitment.html',
}

FAMILY_MAP = {
    '研发族': '技术开发', '销售族': '市场商务', '法务与合规族': '职能',
    '人力资源族': '人力资源', '供应链族': '职能', '财经族': '财务会计',
    '服务族': '职能', '制造族': '技术开发',
}


def clean_city(area):
    """中国/杭州 → 杭州"""
    if not area:
        return '全国'
    parts = [p for p in re.split(r'[/、 ]', area) if p and p != '中国']
    return parts[-1] if parts else area


def fetch_jobs(max_pages=5, page_size=100):
    s = requests.Session()
    s.headers.update(HEADERS)
    s.get(ROOT + '/', timeout=20)  # 拿 JSESSIONID

    items = []
    for page in range(1, max_pages + 1):
        url = API.format(page_size, page) + '?jobType=3&language=zh_CN'
        d = s.get(url, timeout=30).json()
        result = d.get('result', [])
        if not result:
            break
        for j in result:
            items.append({
                'title': j.get('jobname', ''),
                'company': '华为',
                'city': clean_city(j.get('jobArea', '')),
                'job_type': FAMILY_MAP.get(j.get('jobFamilyName', ''), '技术开发'),
                'description': (j.get('mainBusiness') or j.get('mostlyDuty') or '')[:5000],
                'requirements': (j.get('jobRequire') or j.get('demand') or '')[:3000],
                'contact_info': '🔗 原文链接：' + DETAIL.format(j.get('jobId', ''), j.get('dataSource', '')),
                'education': (j.get('degree') or '本科及以上'),
                'days_per_week': 4, 'duration_months': 3,
                'tags': ['华为', '大厂'],
            })
        total = d.get('pageVO', {}).get('totalRows', 0)
        if page * page_size >= total:
            break
    return items


def main():
    items = fetch_jobs()
    print(f'提取 {len(items)} 条华为岗位')
    for it in items:
        print(f'  {it["title"][:30]} | {it["city"]} | {it["job_type"]} | desc:{len(it["description"])} req:{len(it["requirements"])}')

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
    else:
        print('（当前华为校招在招岗位极少，季节开放后会自动抓更多）')


if __name__ == '__main__':
    main()
