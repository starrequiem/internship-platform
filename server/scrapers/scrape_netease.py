"""
网易校招/实习 — 直连 campus.163.com 公开 API

接口: GET /api/campuspc/position/getJobList?pageSize&currentPage&projectId
项目: 从 GET /api/campuspc/project/navigation/list 动态获取 campus.163.com 的项目 ID

用法: python scrape_netease.py [--max-pages 20]
"""
import json
import os
import sys
import io
import re
import time
import argparse
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from inserter import insert_item, get_conn

BASE = 'https://campus.163.com'
NAV_API = BASE + '/api/campuspc/project/navigation/list'
JOB_API = BASE + '/api/campuspc/position/getJobList'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': BASE + '/app/job/position',
}

# 网易 positionTypeName → 岗位类型
FAMILY_MAP = [
    ('算法', '算法/AI'), ('人工智能', '算法/AI'), ('AI', '算法/AI'),
    ('数据', '数据分析'), ('大数据', '数据分析'),
    ('技术', '技术开发'), ('研发', '技术开发'), ('开发', '技术开发'),
    ('测试', '技术开发'), ('运维', '技术开发'), ('安全', '技术开发'),
    ('硬件', '硬件芯片'), ('芯片', '硬件芯片'), ('嵌入式', '硬件芯片'),
    ('机械', '工科类'), ('电气', '工科类'), ('材料', '工科类'), ('自动化', '工科类'),
    ('产品', '产品经理'), ('游戏策划', '产品经理'),
    ('设计', 'UI/UX 设计'), ('UI', 'UI/UX 设计'), ('视觉', 'UI/UX 设计'),
    ('运营', '运营'),
    ('内容', '新闻媒体'), ('新媒体', '新闻媒体'), ('传媒', '新闻媒体'),
    ('市场', '市场商务'), ('营销', '市场商务'), ('销售', '市场商务'), ('商务', '市场商务'),
    ('人力资源', '人力资源'), ('HR', '人力资源'), ('招聘', '人力资源'),
    ('金融', '金融投资'), ('投资', '金融投资'),
    ('财务', '财务会计'), ('会计', '财务会计'), ('审计', '财务会计'),
    ('法务', '法务合规'), ('法律', '法务合规'), ('合规', '法务合规'),
    ('职能', '职能支持'), ('行政', '职能支持'), ('采购', '职能支持'),
]


def classify(ptype):
    if not ptype:
        return '技术开发'
    for kw, jt in FAMILY_MAP:
        if kw.lower() in ptype.lower():
            return jt
    return '技术开发'


def get_project_ids():
    """从导航接口动态获取 campus.163.com 的项目 ID"""
    try:
        r = requests.get(NAV_API + '?timeStamp=' + str(int(time.time() * 1000)),
                         headers=HEADERS, timeout=20)
        d = r.json()
        ids = []
        for group in (d.get('data') or []):
            for child in (group.get('children') or []):
                link = child.get('link') or ''
                m = re.search(r'[?&]id=(\d+)', link)
                if m and ('campus.163.com' in link or 'campus.game.163.com' in link):
                    pid = int(m.group(1))
                    if pid not in ids:
                        ids.append(pid)
        return ids
    except Exception as e:
        print(f'  获取项目列表失败: {e}')
        return [69, 76]  # 兜底：网易互联网2026届 / 智邮27届精英实习生


def fetch_jobs(max_pages=20, page_size=100):
    items = []
    project_ids = get_project_ids()
    print(f'  项目 ID: {project_ids}')
    for pid in project_ids:
        for page in range(1, max_pages + 1):
            url = (f'{JOB_API}?pageSize={page_size}&currentPage={page}'
                   f'&projectId={pid}&timeStamp={int(time.time() * 1000)}')
            try:
                d = requests.get(url, headers=HEADERS, timeout=30).json()
            except Exception as e:
                print(f'  projectId={pid} page={page} 请求失败: {e}')
                break
            data = d.get('data') or {}
            lst = data.get('list') or []
            if not lst:
                break
            for j in lst:
                cities = (j.get('workPlaceName') or '').split(',')
                city = cities[0].strip() if cities and cities[0].strip() else '全国'
                ptype = j.get('positionTypeName') or ''
                items.append({
                    'title': j.get('positionName', ''),
                    'company': '网易',
                    'city': city,
                    'job_type': classify(ptype),
                    'description': (j.get('positionDescription') or '')[:5000],
                    'requirements': (j.get('positionRequirement') or '')[:3000],
                    'contact_info': '🔗 原文链接：' + BASE + '/app/job/position?id=' + str(pid),
                    'education': '本科及以上',
                    'days_per_week': 4, 'duration_months': 3,
                    'tags': ['网易', '大厂', ptype],
                })
            total = data.get('total', 0)
            if page * page_size >= total:
                break
        print(f'  projectId={pid}: 累计 {sum(1 for x in items)} 条')
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--max-pages', type=int, default=20)
    args = ap.parse_args()
    items = fetch_jobs(args.max_pages)
    print(f'\n提取 {len(items)} 条网易岗位')
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
