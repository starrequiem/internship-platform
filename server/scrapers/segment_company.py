"""
大厂整页文本分割 — 把整页正文按「职位 ID」边界拆成结构化岗位，入库

针对字节跳动校招列表页的文本结构：
  [岗位名]
  [城市 实习/正式 类别 招聘项目 职位 ID：AXXXX]
  [团队介绍 + 1、2、3... 职责]

用法: python segment_company.py
"""
import json
import os
import sys
import io
import re
import glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from config import CITIES
from extract import _is_list_item
from inserter import insert_item, get_conn

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'raw_pages')
PARSED_DIR = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'parsed_ai')
SOURCE_URL = 'https://jobs.bytedance.com/campus/position'

# 职责编号列表之前的通用说明标签（团队介绍/项目说明等，非职位描述本身）
NOISE_LABELS = ['团队介绍', '日常实习', 'ByteIntern', '项目说明', '课题介绍', '导师介绍', '项目亮点']

# 字节页尾导航（仅出现在页脚，用于截断最后一个岗位之后的内容）
FOOTER_KEYS = ['联系我们', '相关网站', '候选人反馈平台', '官网使用体验反馈', '字节跳动 Seed']


def _extract_desc(lines):
    """从某岗位正文行里提取「职位描述」：优先取职责编号列表（1、2、3…），
    跳过前置的团队介绍/项目说明等噪音，并去掉尾部的分页页码（如 1/2/3…752）。"""
    start = None
    for i, l in enumerate(lines):
        if _is_list_item(l):
            start = i
            break
    if start is None:
        out = [l for l in lines if not any(n in l for n in NOISE_LABELS)]
    else:
        out = list(lines[start:])
    # 去掉尾部分页页码（纯数字行）
    while out and re.fullmatch(r'\d{1,4}', out[-1]):
        out.pop()
    return '\n'.join(out).strip()


def parse_meta(meta):
    """从 '上海实习运营日常实习职位 ID：A33788A' 提取 城市/类型/类别/职位ID"""
    m = re.search(r'(.*?)\s*职位\s*ID\s*[：:]\s*([A-Za-z0-9]+)', meta)
    head = (m.group(1) if m else meta).strip()
    jid = m.group(2) if m else ''
    cities = [c for c in CITIES if c in head]
    is_intern = '实习' in head
    return head, jid, cities, is_intern


def classify(head):
    rules = [
        ('运营', ['运营', '主播']),
        ('产品经理', ['产品', '游戏策划', '策划']),
        ('UI/UX 设计', ['设计', 'UI', 'UX']),
        ('市场商务', ['销售', '市场', '商务']),
        ('数据分析', ['数据', '分析']),
        ('技术开发', ['研发', '算法', '后端', '前端', '客户端', '测试', '运维', '安全', '开发', '工程', '编译器', '芯片']),
        ('人力资源', ['HR', '人力']),
    ]
    for jt, kws in rules:
        if any(k in head for k in kws):
            return jt
    return '技术开发'


def segment(text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    # 截断页尾导航，避免最后一个岗位的描述混入页脚
    cut = len(lines)
    for i, l in enumerate(lines):
        if any(k in l for k in FOOTER_KEYS):
            cut = i
            break
    lines = lines[:cut]
    meta_idx = [i for i, l in enumerate(lines) if '职位 ID' in l]
    items = []
    for k, mi in enumerate(meta_idx):
        title = lines[mi - 1] if mi > 0 else ''
        head, jid, cities, is_intern = parse_meta(lines[mi])
        desc_start = mi + 1
        desc_end = meta_idx[k + 1] - 1 if k + 1 < len(meta_idx) else len(lines)
        desc = _extract_desc(lines[desc_start:desc_end])
        items.append({
            'title': title,
            'company': '字节跳动',
            'city': cities[0] if cities else '全国',
            'district': '',
            'job_type': classify(head),
            'description': desc,
            'requirements': '',
            'contact_info': '🔗 原文链接：' + SOURCE_URL,
            'education': '本科及以上',
            'days_per_week': 4,
            'duration_months': 3,
            'tags': ['字节跳动', '大厂'] + (['实习'] if is_intern else []),
        })
    return items


def main():
    files = sorted(glob.glob(os.path.join(RAW_DIR, 'default_0_*.json')))
    if not files:
        print('未找到 default_0_*.json（字节跳动整页），请先运行 scraper.py --site default')
        return
    data = json.load(open(files[-1], encoding='utf-8'))
    items = segment(data.get('text', ''))
    print(f'分割出 {len(items)} 条岗位：')
    for it in items:
        print(f'  {it["title"][:32]} | {it["city"]} | {it["job_type"]} | desc:{len(it["description"])}字')

    os.makedirs(PARSED_DIR, exist_ok=True)
    out = os.path.join(PARSED_DIR, 'bytedance_segmented.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'items': items, 'count': len(items)}, f, ensure_ascii=False, indent=2)
    print(f'\n已保存 {out}')

    conn = get_conn()
    ins = skip = 0
    for it in items:
        try:
            if insert_item(it):
                ins += 1
            else:
                skip += 1
        except Exception as e:
            print(f'  ✖ {it["title"][:20]}: {e}')
            skip += 1
    print(f'\n入库: 新增 {ins} | 跳过 {skip}')


if __name__ == '__main__':
    main()
