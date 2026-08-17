"""
入库模块  将结构化实习数据写入 MySQL
"""
import sys, os, json, re

# 读取 .env 配置
ENV_FILE = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

import pymysql

# 复用同一个数据库连接
_conn = None

def get_conn():
    global _conn
    if _conn is None or not _conn.open:
        _conn = pymysql.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASSWORD', '200619'),
            database=os.environ.get('DB_NAME', 'internship_platform'),
            charset='utf8mb4',
            autocommit=True,
        )
        print(f' MySQL 连接成功: {os.environ.get("DB_HOST","localhost")}/{os.environ.get("DB_NAME","internship_platform")}')
    return _conn


def insert_item(item, default_poster_id=1):
    """插入单条，去重: title + company"""
    title   = (item.get('title') or '').strip()
    company = (item.get('company') or '').strip()
    city    = item.get('city', '') or ''
    job_type = item.get('job_type', '') or '技术开发'
    desc    = item.get('description', '') or ''
    reqs    = item.get('requirements', '') or ''
    salary_min = item.get('salary_min')
    salary_max = item.get('salary_max')
    education  = item.get('education', '') or '本科及以上'
    # 联系信息：优先用已有的 contact_info，否则从 url/email 拼装
    contact_info = item.get('contact_info', '') or ''
    if not contact_info:
        url = item.get('url', '') or item.get('apply_url', '') or item.get('source_url', '') or ''
        email = item.get('apply_email', '') or ''
        parts = []
        if url: parts.append('🔗 原文链接：' + url)
        if email: parts.append('📧 投递邮箱：' + email)
        if not parts:
            company = item.get('company', '') or ''
            title = item.get('title', '') or ''
            parts.append('💡 请在招聘网站搜索「' + company + ' ' + title + '」查看原文和投递方式')
        contact_info = '\n'.join(parts)
    deadline   = item.get('deadline') or None
    apply_time = item.get('apply_time') or ''
    headcount  = item.get('headcount') or 1

    if not title or not company:
        return None

    conn = get_conn()
    cur = conn.cursor()

    # 去重: title + company + city 三字段联合唯一
    cur.execute(
        'SELECT id, description, requirements, deadline, apply_time, salary_min, salary_max FROM internships WHERE title = %s AND company = %s AND city = %s LIMIT 1',
        [title, company, city]
    )
    existing = cur.fetchone()

    if existing:
        eid, old_desc, old_reqs, old_deadline, old_apply_time, old_min, old_max = existing
        old_desc = old_desc or ''
        old_reqs = old_reqs or ''
        old_apply_time = old_apply_time or ''

        # 二次校验: 如果新旧描述差异很大(>50%不同), 视为不同岗位
        if desc and old_desc:
            similarity = text_similarity(desc[:500], old_desc[:500])
            if similarity < 0.5:
                print(f'   [NEW] #{eid} has same title+company+city but different content (similarity={similarity:.2f})')
                existing = None

        if existing:
            parts = []
            vals = []

            if desc and len(desc) > len(old_desc):
                parts.append('description = %s'); vals.append(desc[:5000])
            if reqs and len(reqs) > len(old_reqs):
                parts.append('requirements = %s'); vals.append(reqs[:3000])
            if deadline and not old_deadline:
                parts.append('deadline = %s'); vals.append(deadline)
            if apply_time and not old_apply_time:
                parts.append('apply_time = %s'); vals.append(apply_time)
            if (salary_min or salary_max) and not (old_min or old_max):
                parts.append('salary_min = %s, salary_max = %s')
                vals.extend([salary_min, salary_max])

            if parts:
                vals.append(eid)
                cur.execute('UPDATE internships SET ' + ', '.join(parts) + ' WHERE id = %s', vals)
                print(f'   [UPDATE] #{eid} {company} - {title} ({len(parts)} fields enriched)')
            else:
                print(f'   [SKIP] #{eid} {company} - {title} (no new data)')
            return eid

    # --- 新增记录 ---
    if not existing:
        # 标签匹配
        tags = match_tags(title, desc, job_type)

        # 插入
        cur.execute(
            '''INSERT INTO internships
               (poster_id, title, company, city, job_type, salary_min, salary_max,
                education, days_per_week, duration_months, headcount, deadline, apply_time,
                description, requirements, contact_info, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            [default_poster_id, title, company, city, job_type,
             salary_min, salary_max, education,
             4, 3, headcount, deadline, apply_time,
             desc[:5000], reqs[:3000],
             contact_info[:2000], 'active']
        )
        new_id = cur.lastrowid

        # 关联标签
        for tag_name in tags[:8]:
            cur.execute('INSERT IGNORE INTO tags (name) VALUES (%s)', [tag_name])
            cur.execute('SELECT id FROM tags WHERE name = %s', [tag_name])
            tag_row = cur.fetchone()
            if tag_row:
                cur.execute(
                    'INSERT IGNORE INTO internship_tags (internship_id, tag_id) VALUES (%s,%s)',
                    [new_id, tag_row[0]]
                )

        print(f'   [INSERT] #{new_id} {company} - {title} | {city} | {job_type}')
        return new_id


def text_similarity(a, b):
    """快速文本相似度 (0~1)，基于共同单词比例"""
    if not a or not b:
        return 0
    set_a = set(a.lower().split())
    set_b = set(b.lower().split())
    if not set_a or not set_b:
        return 0
    intersection = set_a & set_b
    return len(intersection) / min(len(set_a), len(set_b))


def match_tags(title, desc, job_type):
    text = f'{title} {desc} {job_type}'.lower()
    tags = []
    tag_map = {
        'react': 'React', 'vue': 'Vue', 'typescript': 'TypeScript',
        'javascript': 'JavaScript', 'node': 'Node.js', 'python': 'Python',
        'java': 'Java', 'go': 'Go', 'golang': 'Go', 'c++': 'C/C++',
        'spring': 'Spring', 'django': 'Django', 'pytorch': 'PyTorch',
        'k8s': 'K8s', 'kubernetes': 'K8s', 'docker': 'Docker',
        'sql': 'SQL', '转正': '可转正', '远程': '远程办公', '导师': '导师带教',
        '三餐': '免费三餐', '大模型': 'LLM', 'AI': 'AI',
    }
    for key, tag in tag_map.items():
        if key in text and tag not in tags:
            tags.append(tag)
    # 大厂标签
    big = ['字节跳动','腾讯','阿里巴巴','美团','华为','百度','小红书','快手','京东','网易']
    for c in big:
        if c.lower() in text:
            if '大厂' not in tags: tags.append('大厂')
            break
    return tags


def insert_from_file(filepath):
    """从 JSON 文件读取并入库"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data.get('items', [])
    inserted = 0
    skipped = 0
    for item in items:
        try:
            rid = insert_item(item)
            if rid: inserted += 1
            else: skipped += 1
        except Exception as e:
            print(f'   {item.get("title","?")}: {e}')
            skipped += 1
    return inserted, skipped


def run_insert():
    """入库所有 parsed 目录的 JSON，返回 (新增, 跳过)。供 main.py insert 与命令行调用。"""
    parsed_dir = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'parsed')
    total_in, total_skip = 0, 0
    if os.path.isdir(parsed_dir):
        for fname in os.listdir(parsed_dir):
            if fname.endswith('.json'):
                print(f'\n {fname}')
                a, b = insert_from_file(os.path.join(parsed_dir, fname))
                total_in += a; total_skip += b
    print(f'\n 入库:  {total_in} 新增 |  {total_skip} 跳过')
    return total_in, total_skip


if __name__ == '__main__':
    run_insert()
