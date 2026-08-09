"""
牛客网专用解析器 - 从列表页文本提取结构化实习信息
"""
import re, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from config import COMPANIES, CITIES, CLASSIFY_RULES

def parse_nowcoder_text(text):
    """Parse Nowcoder job list text into structured items"""
    items = []
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect job entry: line contains salary pattern
        salary_match = re.search(r'(\d+)\s*[-~至]\s*(\d+)\s*元/[天日]', line)
        is_mianyi = '面议' in line

        if (salary_match or is_mianyi) and i > 0:
            item = extract_job_entry(lines, i, salary_match, is_mianyi)
            if item:
                items.append(item)
        i += 1

    return items

def extract_job_entry(lines, salary_idx, salary_match, is_mianyi):
    """Extract a single job entry around a salary line"""
    item = {
        'title': '',
        'company': '',
        'city': '',
        'job_type': '',
        'salary_min': None,
        'salary_max': None,
        'education': '本科及以上',
        'days_per_week': 4,
        'duration_months': 3,
        'description': '',
    }

    # Salary
    if salary_match:
        item['salary_min'] = int(salary_match.group(1))
        item['salary_max'] = int(salary_match.group(2))

    # Look backwards for job title (the line just before salary, or 2-3 lines back)
    title = ''
    for j in range(salary_idx - 1, max(salary_idx - 4, -1), -1):
        candidate = lines[j]
        # Skip badge lines (薪资超XX%, HR刚处理, etc.)
        if any(b in candidate for b in ['薪资超', 'HR', '助力', '兼顾', '暑假', '直达', '投后', '校招高薪', '牛客指数']):
            continue
        if '元/天' in candidate or '面议' in candidate:
            continue
        if len(candidate) < 5:
            continue
        title = candidate.strip()
        break
    item['title'] = title

    # Look forward for city, days, company
    for j in range(salary_idx + 1, min(salary_idx + 12, len(lines))):
        line = lines[j]

        # City
        if not item['city']:
            for c in CITIES:
                if c in line:
                    item['city'] = c
                    break

        # Work days
        days_match = re.search(r'(\d+)\s*天/周', line)
        if days_match:
            item['days_per_week'] = int(days_match.group(1))

        # Duration
        dur_match = re.search(r'(?:最少|至少)?\s*(\d+)\s*(?:个)?月', line)
        if dur_match:
            item['duration_months'] = int(dur_match.group(1))

        # Education
        if '博士' in line:
            item['education'] = '博士'
        elif '硕士' in line:
            item['education'] = '硕士及以上'
        elif '本科' in line:
            item['education'] = '本科及以上'

        # Company
        if not item['company']:
            for comp in COMPANIES:
                if comp in line:
                    item['company'] = comp
                    break
            # Also check for company-like lines (2-10 chars, no common words)
            if not item['company'] and 2 <= len(line) <= 20 and not any(
                w in line for w in ['元/天', '面议', '薪资', '助力', '直达', '投后', 'HR', '暂无', '牛客']
            ):
                # Check if it looks like a company name
                if not re.search(r'[\d.,，。！!]', line):
                    # Might be a smaller company
                    pass

    # Job type classification
    if item['title']:
        item['job_type'] = classify_job_type(item['title'])

    # Description: combine surrounding lines
    desc_lines = []
    for j in range(max(0, salary_idx - 1), min(salary_idx + 10, len(lines))):
        l = lines[j].strip()
        if l and len(l) > 3:
            desc_lines.append(l)
    item['description'] = '\n'.join(desc_lines)[:2000]

    # Contact info: construct from URL and email, fallback to source_url
    contact_parts = []
    if item.get('url'):
        contact_parts.append('🔗 原文链接：' + item['url'])
    if item.get('apply_email'):
        contact_parts.append('📧 投递邮箱：' + item['apply_email'])
    if not contact_parts:
        company = item.get('company', '') or ''
        title = item.get('title', '') or ''
        source_url = item.get('source_url', '')
        if source_url:
            contact_parts.append('🔗 牛客网搜索页：' + source_url)
            contact_parts.append('💡 请在页面中搜索「' + company + ' ' + title + '」找到对应岗位后投递')
        else:
            contact_parts.append('🔗 请在牛客网搜索「' + company + ' ' + title + '」查看原文和投递方式')
    item['contact_info'] = '\n'.join(contact_parts)

    # Only return if at least title or company found
    if item['title'] or item['company']:
        return item
    return None

def classify_job_type(title):
    """Classify job type from title"""
    for job_type, keywords in CLASSIFY_RULES['job_type'].items():
        for kw in keywords:
            if kw.lower() in title.lower():
                return job_type
    return '技术开发'  # default for Nowcoder listings

if __name__ == '__main__':
    # Parse the Nowcoder targeted data
    files = [
        '../scraped_data/targeted/nowcoder_1786005399.json',
        '../scraped_data/targeted/xybsyw_1786005405.json',
    ]

    for fpath in files:
        if not os.path.exists(fpath):
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        text = data.get('raw_text', '')
        source_url = data.get('url', '')
        items = parse_nowcoder_text(text)
        # Inject source_url into each item for contact_info fallback
        for item in items:
            if not item.get('url'):
                item['source_url'] = source_url
        data['items'] = items
        data['status'] = 'parsed'

        print(f'{os.path.basename(fpath)}: {len(items)} items')
        for item in items[:5]:
            sal = f'{item["salary_min"]}-{item["salary_max"]}/day' if item['salary_min'] else 'negotiable'
            print(f'  [{item["job_type"]}] {item["company"]} {item["title"][:40]} | {item["city"]} | {sal}')

        # Save back
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print('\nDone!')
