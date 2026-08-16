"""
JobSpy 爬虫 — 多平台抓取实习信息，自带投递链接
支持: LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google
输出: JSON 文件，每条含 contact_info（投递链接）
"""
import json, os, sys, time, re
import pandas as pd
from jobspy import scrape_jobs

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'jobspy')
os.makedirs(OUT_DIR, exist_ok=True)

# 搜索关键词（国内+国际）
SEARCHES = [
    # 国内大厂
    {"site": "linkedin", "term": "software engineer intern", "location": "Beijing, China", "results": 30},
    {"site": "linkedin", "term": "software engineer intern", "location": "Shanghai, China", "results": 30},
    {"site": "linkedin", "term": "software engineer intern", "location": "Shenzhen, China", "results": 20},
    {"site": "linkedin", "term": "data science intern", "location": "Beijing, China", "results": 20},
    {"site": "linkedin", "term": "product manager intern", "location": "China", "results": 20},
    # 国际
    {"site": "indeed", "term": "software engineer intern", "location": "United States", "results": 20},
    {"site": "glassdoor", "term": "software engineer intern", "location": "United States", "results": 20},
]

CLASSIFY_RULES = {
    '技术开发': ['software','engineer','developer','开发','前端','后端','全栈','java','python','react','golang','web','frontend','backend','fullstack','算法','AI','machine learning'],
    '产品经理': ['product manager','产品','pm'],
    '数据分析': ['data analyst','data science','数据分析','数据科学','business intelligence','bi '],
    'UI/UX 设计': ['designer','设计','ux','ui','graphic'],
    '运营': ['operations','运营','marketing','市场'],
    '人力资源': ['hr','human resources','人力资源','recruiter','talent'],
}

CITIES = ['北京','上海','广州','深圳','杭州','成都','南京','武汉','西安','苏州','远程办公','Beijing','Shanghai','Shenzhen','Guangzhou','Hangzhou','Chengdu','Nanjing']

def classify(title, desc=''):
    text = (title + ' ' + desc).lower()
    for job_type, keywords in CLASSIFY_RULES.items():
        for kw in keywords:
            if kw in text:
                return job_type
    return '技术开发'

def extract_city(location_str):
    if not location_str: return ''
    for c in CITIES:
        if c.lower() in location_str.lower():
            return c
    return location_str.split(',')[0].strip() if location_str else ''

def extract_salary(row):
    """从 JobSpy 输出提取薪资"""
    try:
        if pd.notna(row.get('min_amount')) and pd.notna(row.get('max_amount')):
            interval = str(row.get('interval', '')).lower()
            if 'hour' in interval:
                return int(row['min_amount']) * 8, int(row['max_amount']) * 8  # 估算日薪
            elif 'month' in interval:
                return int(row['min_amount'] / 22), int(row['max_amount'] / 22)
            elif 'year' in interval:
                return int(row['min_amount'] / 250), int(row['max_amount'] / 250)
            else:
                return int(row['min_amount']), int(row['max_amount'])
    except:
        pass
    return None, None

def extract_deadline(row):
    """从 date_posted 推算截止日期（通常30天后）"""
    try:
        if pd.notna(row.get('date_posted')):
            from datetime import datetime, timedelta
            posted = pd.Timestamp(row['date_posted']).to_pydatetime()
            return (posted + timedelta(days=30)).strftime('%Y-%m-%d')
    except:
        pass
    return None

def scrape_and_convert(site, term, location, results=20):
    """抓取并转换为标准格式"""
    items = []
    try:
        print(f'  [{site}] "{term}" @ {location} ...')
        jobs = scrape_jobs(
            site_name=[site],
            search_term=term,
            location=location,
            results_wanted=results,
            hours_old=720,  # 30 days
            linkedin_fetch_description=True,
        )

        if jobs is None or len(jobs) == 0:
            print(f'    → 0 results')
            return items

        for _, row in jobs.iterrows():
            title = str(row.get('title', '')).strip()
            company = str(row.get('company', '')).strip()
            location_str = str(row.get('location', '')).strip()
            desc = str(row.get('description', '')).strip()

            if not title or not company:
                continue

            # 投递链接 — JobSpy 原生提供
            apply_url = str(row.get('job_url', '') or row.get('job_url_direct', '')).strip()

            sal_min, sal_max = extract_salary(row)
            city = extract_city(location_str)
            job_type = classify(title, desc)
            deadline = extract_deadline(row)

            # 构建 contact_info
            contact_parts = []
            if apply_url:
                contact_parts.append('🔗 原文投递链接：' + apply_url)
            if not contact_parts:
                contact_parts.append('💡 搜索「' + company + ' ' + title + '」查看投递方式')

            items.append({
                'title': title,
                'company': company,
                'city': city or '远程办公',
                'job_type': job_type,
                'salary_min': sal_min,
                'salary_max': sal_max,
                'description': desc[:3000],
                'requirements': '',
                'education': '本科及以上',
                'days_per_week': 4,
                'duration_months': 3,
                'deadline': deadline,
                'headcount': 1,
                'contact_info': '\n'.join(contact_parts),
                'url': apply_url,  # 额外保留供 inserter 使用
                'source': site,
            })

        print(f'    → {len(items)} items')
        return items

    except Exception as e:
        print(f'    ✖ Error: {e}')
        return items


def main():
    all_items = []
    for s in SEARCHES:
        items = scrape_and_convert(s['site'], s['term'], s['location'], s['results'])
        all_items.extend(items)
        time.sleep(2)  # rate limit

    # 去重（同 title + company）
    seen = set()
    unique = []
    for item in all_items:
        key = (item['title'].lower(), item['company'].lower())
        if key not in seen:
            seen.add(key)
            unique.append(item)

    print(f'\n总计: {len(unique)} 条 (去重后)')

    # 保存
    fname = os.path.join(OUT_DIR, f'jobs_{int(time.time())}.json')
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump({'items': unique, 'count': len(unique)}, f, ensure_ascii=False, indent=2)
    print(f'Saved: {fname}')


if __name__ == '__main__':
    main()
