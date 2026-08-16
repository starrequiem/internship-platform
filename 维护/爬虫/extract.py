"""
详情页文本分割 — 从整页正文里稳健地拆出「职位描述」「任职要求」

牛客等招聘站详情页把 标题/薪资/公司/职位描述/任职要求 混在同一段正文里，
之前的「上一个兄弟元素」定位方式在页面改版后会抓到 59 字符碎片。
这里改为按标题关键词边界逐行切分，容错性更好。
"""

DESC_KEYS = ['职位描述', '岗位职责', '工作内容', '岗位描述', '职位详情', '职责描述']
REQ_KEYS = ['任职要求', '岗位要求', '职位要求', '任职资格', '加分项', '任职条件']
STOP_KEYS = ['公司介绍', '工作地址', '工作地点', '投递方式', '职位base', '职位Base',
             '福利待遇', '薪资待遇', '薪酬福利', '简历投递', '联系方式', '发布时间']


def _content_after_title(line, keys):
    """若标题行本身带内容（如「职位描述：xxx」），返回冒号后的内容，否则返回空串"""
    for sep in ('：', ':', ':'):
        if sep in line:
            head, tail = line.split(sep, 1)
            if any(k in head for k in keys) and tail.strip():
                return tail.strip()
    return ''


def split_detail(text):
    """从整页文本提取 (description, requirements)。返回两个字符串。"""
    if not text:
        return '', ''
    desc, req = [], []
    section = None  # None | 'desc' | 'req'
    for raw in text.split('\n'):
        line = raw.strip()
        if not line:
            continue

        if any(k in line for k in DESC_KEYS):
            section = 'desc'
            extra = _content_after_title(line, DESC_KEYS)
            if extra:
                desc.append(extra)
            continue
        if any(k in line for k in REQ_KEYS):
            section = 'req'
            extra = _content_after_title(line, REQ_KEYS)
            if extra:
                req.append(extra)
            continue
        if any(k in line for k in STOP_KEYS):
            section = None
            continue

        if section == 'desc':
            desc.append(line)
        elif section == 'req':
            req.append(line)

    return '\n'.join(desc).strip(), '\n'.join(req).strip()
