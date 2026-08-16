"""
牛客网解析器 — 从列表页文本和链接提取结构化实习信息
"""
import re, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from config import COMPANIES, CITIES, CLASSIFY_RULES, extract_company_fallback

def parse_nowcoder_text(text):
    """从牛客网文本提取结构化数据"""
    items = []
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    i = 0
    while i < len(lines):
        line = lines[i]
        salary_match = re.search(r'(\d+)\s*[-~至]\s*(\d+)\s*元/[天日]', line)
        is_mianyi = '面议' in line
        if (salary_match or is_mianyi) and i > 0:
            item = extract_job_entry(lines, i, salary_match, is_mianyi)
            if item: items.append(item)
        i += 1
    return items

def extract_job_entry(lines, salary_idx, salary_match, is_mianyi):
    item = {'title':'','company':'','city':'','job_type':'','salary_min':None,'salary_max':None,
            'education':'本科及以上','days_per_week':4,'duration_months':3,'description':''}
    if salary_match:
        item['salary_min'] = int(salary_match.group(1))
        item['salary_max'] = int(salary_match.group(2))
    title = ''
    for j in range(salary_idx - 1, max(salary_idx - 4, -1), -1):
        candidate = lines[j]
        if any(b in candidate for b in ['薪资超','HR','助力','兼顾','暑假','直达','投后','校招高薪','牛客指数']): continue
        if '元/天' in candidate or '面议' in candidate: continue
        if len(candidate) < 3: continue
        title = candidate.strip()
        break
    item['title'] = title
    for j in range(salary_idx + 1, min(salary_idx + 12, len(lines))):
        line = lines[j]
        if not item['city']:
            for c in CITIES:
                if c in line: item['city'] = c; break
        days_match = re.search(r'(\d+)\s*天/周', line)
        if days_match: item['days_per_week'] = int(days_match.group(1))
        dur_match = re.search(r'(?:最少|至少)?\s*(\d+)\s*(?:个)?月', line)
        if dur_match: item['duration_months'] = int(dur_match.group(1))
        if '博士' in line: item['education'] = '博士'
        elif '硕士' in line: item['education'] = '硕士及以上'
        elif '本科' in line: item['education'] = '本科及以上'
        if not item['company']:
            for comp in COMPANIES:
                if comp in line: item['company'] = comp; break
    desc_lines = []
    for j in range(max(0, salary_idx - 1), min(salary_idx + 10, len(lines))):
        l = lines[j].strip()
        if l and len(l) > 3: desc_lines.append(l)
    item['description'] = '\n'.join(desc_lines)[:2000]
    if item['title']: item['job_type'] = classify_job_type(item['title'])
    if item['title'] or item['company']: return item
    return None

def classify_job_type(title):
    for job_type, keywords in CLASSIFY_RULES['job_type'].items():
        for kw in keywords:
            if kw.lower() in title.lower(): return job_type
    return '技术开发'

def parse_from_links(job_links, source_url=''):
    """
    从 job_links 直接构建 items。
    每个 job_link: {title: '岗位名 薪资 城市..', url: 'https://...'}
    """
    items = []
    for jl in job_links:
        title_text = jl.get('title', '')
        url = jl.get('url', '')
        if not title_text: continue

        lines = title_text.split('\n')

        # 第一行是岗位名
        job_title = lines[0].strip() if lines else title_text

        # 提取薪资
        salary_match = re.search(r'(\d+)\s*[-~至]\s*(\d+)\s*元/[天日]', title_text)
        sal_min = int(salary_match.group(1)) if salary_match else None
        sal_max = int(salary_match.group(2)) if salary_match else None

        # 提取城市
        city = ''
        for c in CITIES:
            if c in title_text:
                city = c
                break

        # 提取公司（从所有行中找，包括第一行）
        company = ''
        all_text = title_text
        for comp in sorted(COMPANIES, key=len, reverse=True):  # 优先匹配长公司名
            if comp in all_text:
                company = comp
                break
        if not company:
            company = extract_company_fallback(title_text)  # 兜底按后缀提取

        # 提取每周天数
        days = 4
        dm = re.search(r'(\d+)\s*天/周', title_text)
        if dm: days = int(dm.group(1))

        job_type = classify_job_type(job_title)

        # 构建 contact_info
        contact_info = '🔗 牛客网投递链接：' + url

        items.append({
            'title': job_title[:200],
            'company': company or extract_company_fallback(title_text) or '待识别',
            'city': city or '全国',
            'job_type': job_type,
            'salary_min': sal_min,
            'salary_max': sal_max,
            'education': '本科及以上',
            'days_per_week': days,
            'duration_months': 3,
            'description': title_text[:2000],
            'requirements': '',
            'contact_info': contact_info,
            'url': url,
        })

    return items


if __name__ == '__main__':
    import glob
    files = glob.glob('../scraped_data/targeted/nowcoder_*.json')
    if not files:
        files = glob.glob('../scraped_data/targeted/xybsyw_*.json')

    for fpath in files:
        if not os.path.exists(fpath): continue
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        text = data.get('raw_text', '')
        job_links = data.get('job_links', [])
        source_url = data.get('url', '')

        # 优先从job_links解析，否则从文本解析
        if job_links:
            items = parse_from_links(job_links, source_url)
            print(f'{os.path.basename(fpath)}: {len(items)} items (from job_links)')
        else:
            items = parse_nowcoder_text(text)
            for item in items:
                if not item.get('url'): item['source_url'] = source_url
            print(f'{os.path.basename(fpath)}: {len(items)} items (from text)')

        data['items'] = items
        data['status'] = 'parsed'

        for item in items[:3]:
            sal = f'{item["salary_min"]}-{item["salary_max"]}/day' if item['salary_min'] else 'negotiable'
            url = item.get('url', '') or item.get('source_url', '')
            print(f'  [{item["job_type"]}] {item["company"]} {item["title"][:30]} | {sal} | URL: {url[:50]}...')

        # 保存到 parsed 目录供 inserter 使用
        parsed_dir = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'parsed')
        os.makedirs(parsed_dir, exist_ok=True)
        out_path = os.path.join(parsed_dir, os.path.basename(fpath))
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print('\nDone!')
