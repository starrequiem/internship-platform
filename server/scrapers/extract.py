"""
详情页文本分割 — 从整页正文里稳健地拆出「职位描述」「任职要求」「投递时间」

牛客等招聘站详情页把 标题/薪资/公司/职位描述/任职要求 混在同一段正文里，
且「职位描述」经常没有标题头（直接以编号列表开始），页尾还夹带大量
导航/安全提示/推荐等噪音。这里分三步处理：
  1. 先按「牛客安全提示 / 页脚导航」等标志截断页尾噪音
  2. 再按「任职要求」标题切出要求段
  3. 描述段内定位编号列表起点，跳过顶部元信息（标题/薪资/城市/HR 状态）
"""

import re

DESC_KEYS = ['职位描述', '岗位职责', '工作内容', '岗位描述', '职位详情', '职责描述', '职位介绍', '工作职责']
REQ_KEYS = ['任职要求', '岗位要求', '职位要求', '任职资格', '加分项', '任职条件', '岗位技能', '技能要求']
STOP_KEYS = ['公司介绍', '工作地址', '工作地点', '投递方式', '职位base', '职位Base',
             '福利待遇', '薪资待遇', '薪酬福利', '简历投递', '联系方式', '发布时间',
             '投递时间', '截止时间', '截止日期', '招聘时间']

# 页尾噪音边界（「牛客安全提示」之后全是页脚/推荐/导航，整段丢弃）
# 注意：不含「关于我们/加入我们/意见反馈」这类常见正文小标题，避免误伤职位描述
FOOTER_KEYS = [
    '牛客安全提示', '如发现虚假招聘', '发现虚假招聘', '立即举报',
    '公司地址', '友情链接', '资源导航', '付费咨询', '校企合作',
    '移动版', '免责声明',
    '笔试题目', '面试短评', '面试经验', '查看其他', '回到顶部',
    'ICP', '备案', '版权所有',
]

# 编号 / 项目符号列表项（职位描述与任职要求通常以编号列表呈现）
_NUM = re.compile(r'^\s*(\d{1,2})\s*[.、．)）]\s*\S')
_BULLET = re.compile(r'^\s*[•·●▪◦\-*]\s*\S')


def _is_list_item(line):
    return bool(_NUM.match(line) or _BULLET.match(line))


def _content_after_title(line, keys):
    """若标题行本身带内容（如「职位描述：xxx」），返回冒号后的内容，否则返回空串"""
    for sep in ('：', ':'):
        if sep in line:
            head, tail = line.split(sep, 1)
            if any(k in head for k in keys) and tail.strip():
                return tail.strip()
    return ''


def _match_header(line, keys):
    """精确匹配标题行：整行等于关键词，或关键词后紧跟冒号（如「职位描述：xxx」）。
    避免「职位详情页」这类导航词被误判为「职位详情」标题。"""
    for k in keys:
        if line == k:
            return k
        if line.startswith(k) and line[len(k):len(k) + 1] in ('：', ':'):
            return k
    return None


def extract_apply_time(text):
    """提取「投递时间」区间原文，如 '2026年3月23日-2026年8月31日'。找不到返回空串。"""
    if not text:
        return ''
    m = re.search(r'(?:投递|招聘|申请|报名)时间\s*[:：]\s*([^\n]{4,80})', text)
    return m.group(1).strip() if m else ''


def deadline_from_apply_time(s):
    """从「投递时间」区间解析截止日期（取末尾日期）→ 'YYYY-MM-DD' 或 None。"""
    if not s:
        return None
    # 中文日期：2026年3月23日
    zh = re.findall(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?', s)
    if zh:
        y, m, d = zh[-1]
        return f'{int(y):04d}-{int(m):02d}-{int(d):02d}'
    # 数字日期：2026-03-23 / 2026/3/23 / 2026.3.23
    num = re.findall(r'(\d{4})\s*[-/.]\s*(\d{1,2})\s*[-/.]\s*(\d{1,2})', s)
    if num:
        y, m, d = num[-1]
        return f'{int(y):04d}-{int(m):02d}-{int(d):02d}'
    return None


def _extract_section(lines, header_keys):
    """从一组行里提取正文：
    - 有 header_keys 标题：从标题后开始（含标题行内联内容）
    - 无标题：定位首个编号/项目符号项作为正文起点
    - 遇到 STOP_KEYS 停止
    """
    if not lines:
        return ''

    start = None
    for i, l in enumerate(lines):
        if _match_header(l, header_keys):
            start = i
            break
    if start is None:
        for i, l in enumerate(lines):
            if _is_list_item(l):
                start = i
                break
    if start is None:
        return ''

    out = []
    for l in lines[start:]:
        if header_keys and _match_header(l, header_keys):
            extra = _content_after_title(l, header_keys)
            if extra:
                out.append(extra)
            continue
        if any(k in l for k in STOP_KEYS):
            break
        out.append(l)
    return '\n'.join(out).strip()


def split_detail(text):
    """从整页文本提取 (description, requirements)。返回两个字符串。"""
    if not text:
        return '', ''

    lines = [l.strip() for l in text.split('\n')]
    lines = [l for l in lines if l]

    # 1. 截断页尾噪音（安全提示/页脚导航之后的内容全部丢弃）
    cut = len(lines)
    for i, l in enumerate(lines):
        if any(k in l for k in FOOTER_KEYS):
            cut = i
            break
    lines = lines[:cut]

    # 2. 找「任职要求」边界（描述在它之前，要求在它之后）
    req_idx = None
    for i, l in enumerate(lines):
        if _match_header(l, REQ_KEYS):
            req_idx = i
            break

    head = lines[:req_idx] if req_idx is not None else lines
    tail = lines[req_idx + 1:] if req_idx is not None else []

    desc = _extract_section(head, DESC_KEYS)
    req = _extract_section(tail, ())
    return desc, req
