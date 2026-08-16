"""
后置解析器  对整页抓取的文本进行结构化提取
"""
import re, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))

from config import CLASSIFY_RULES, CITIES, COMPANIES, extract_company_fallback

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'scraped_data')
PARSED_DIR = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'parsed')
os.makedirs(PARSED_DIR, exist_ok=True)


def parse_raw_text(raw_text, source_name=''):
    """
    从原始文本中提取实习信息
    返回: list of dicts [{title, company, city, job_type, ...}]
    """
    if not raw_text:
        return []

    items = []

    # ---- 策略1: 按分隔符拆分文本块 ----
    # 常见分隔: 多个换行、分隔线、卡片边界
    blocks = re.split(r'\n{3,}|(?:\-{5,})|(?:\={5,})', raw_text)
    blocks = [b.strip() for b in blocks if len(b.strip()) > 50]

    if not blocks:
        blocks = [raw_text]  # 无法拆分，整段处理

    for block in blocks:
        item = extract_from_block(block, source_name)
        if item:
            items.append(item)

    # ---- 策略2: 如果拆不出，用关键词边界重新拆 ----
    if len(items) <= 1 and len(raw_text) > 500:
        items = extract_by_keyword_boundary(raw_text, source_name)

    return items


def extract_from_block(text, source_name=''):
    """从单个文本块提取字段"""
    item = {
        'title': '',
        'company': '',
        'city': '',
        'job_type': '',
        'education': '本科及以上',
        'salary_min': None,
        'salary_max': None,
        'description': text[:2000] if len(text) > 2000 else text,
        'requirements': '',
        'source': source_name,
        'status': 'active',
    }

    # 1. 提取公司名
    for comp in COMPANIES:
        if comp.lower() in text.lower():
            item['company'] = comp
            break
    if not item['company']:
        item['company'] = extract_company_fallback(text)

    # 2. 提取城市
    found_cities = [c for c in CITIES if c in text]
    if found_cities:
        item['city'] = found_cities[0]

    # 3. 提取岗位类型
    for job_type, keywords in CLASSIFY_RULES['job_type'].items():
        for kw in keywords:
            if kw.lower() in text.lower():
                item['job_type'] = job_type
                break
        if item['job_type']:
            break

    # 4. 提取学历要求
    for edu, keywords in sorted(CLASSIFY_RULES['education'].items(),
                                 key=lambda x: len(x[1]), reverse=True):
        for kw in keywords:
            if kw in text:
                item['education'] = edu
                break
        if item['education'] != '本科及以上':  # 已匹配到更具体的
            break

    # 5. 提取岗位名称（在 text 开头或公司名附近的短语）
    title = extract_title(text, item.get('company', ''))
    if title:
        item['title'] = title

    # 6. 提取薪资
    salary_match = re.search(
        r'(?:薪资|日薪|月薪|工资|薪酬).*?(\d+)[kK千]?\s*[-~至到]\s*(\d+)[kK千]?',
        text)
    if not salary_match:
        salary_match = re.search(r'[\xa5]\s*(\d+)\s*[-~至到]\s*(\d+)\s*(?:/天|元/天|/日)', text)
    if salary_match:
        item['salary_min'] = int(salary_match.group(1))
        item['salary_max'] = int(salary_match.group(2))

    # 7. 提取发布日期/截止日期
    deadline = re.search(
        r'(?:截止|有效期).*?(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?)',
        text)
    if deadline:
        item['deadline'] = deadline.group(1)

    # 8. 提取招聘人数
    hc = re.search(r'(?:招聘|招|需求)\s*(\d+)\s*(?:人|名|位)', text)
    if hc:
        item['headcount'] = int(hc.group(1))

    # 9. 提取区/详细地址
    district = re.search(r'(?:海淀|朝阳|南山|福田|余杭|浦东|徐汇|天河|武侯|江宁|雁塔|园区)区?', text)
    if district:
        item['district'] = district.group(0)

    # 至少要有岗位名或公司名才算有效
    if not item['title'] and not item['company']:
        return None

    return item


def extract_title(text, company=''):
    """从文本中提取岗位名称"""
    # 常见岗位名模式
    patterns = [
        r'(?:岗位|职位|招聘)[：:]\s*(.+?)(?:[，。\n])',
        r'([\w/\-]+(?:实习|开发|工程|设计|运营|产品|分析|管理|研究|测试)\w*)',
        r'(?:急招|热招|诚聘)\s*(.+?)(?:[，。\n])',
        r'^\s*(.+?(?:生|师|员))\s*$',  # 行首的实习生/工程师/专员
    ]
    for pat in patterns:
        m = re.search(pat, text, re.MULTILINE)
        if m:
            title = m.group(1).strip()
            if 2 < len(title) < 60 and not title.startswith('http'):
                return title
    return ''


def extract_by_keyword_boundary(text, source_name=''):
    """按「岗位名称」「公司」等关键词边界拆分"""
    items = []
    # 寻找可能的条目边界
    boundaries = []
    for kw in ['岗位名称', '职位名称', '招聘岗位', '工作地点', '公司名称']:
        for m in re.finditer(kw, text):
            boundaries.append(m.start())
    boundaries.sort()

    if len(boundaries) >= 2:
        for i in range(len(boundaries) - 1):
            block = text[boundaries[i]:boundaries[i+1]]
            item = extract_from_block(block, source_name)
            if item:
                items.append(item)
        # 最后一块
        block = text[boundaries[-1]:]
        item = extract_from_block(block, source_name)
        if item:
            items.append(item)

    return items


def parse_all_raw():
    """解析所有 scraped_data 目录中的 fulltext 类型文件"""
    results = []
    if not os.path.exists(RAW_DIR):
        print(f'目录不存在: {RAW_DIR}')
        return results

    for fname in os.listdir(RAW_DIR):
        if not fname.endswith('.json') or fname.startswith('parsed'):
            continue
        fpath = os.path.join(RAW_DIR, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if data.get('status') != 'fulltext' or not data.get('raw_text'):
            # 已有结构化数据，直接取 items
            if data.get('items'):
                results.append(data)
            continue

        print(f' 解析: {fname} ({len(data["raw_text"])} 字符)')
        items = parse_raw_text(data['raw_text'], data.get('site', ''))
        data['items'] = items
        data['status'] = 'parsed'

        # 保存解析结果
        parsed_path = os.path.join(PARSED_DIR, fname)
        with open(parsed_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f'   提取 {len(items)} 条  {parsed_path}')
        results.append(data)

    total = sum(len(r.get('items', [])) for r in results)
    print(f'\n 解析汇总: {len(results)} 个文件, 共 {total} 条')
    return results


if __name__ == '__main__':
    parse_all_raw()
