"""默认通用配置 — 大厂官网招聘页

大厂官网页面结构各异，不适合写死选择器。
策略：整页文本抓下来，先交给 AI 做信息分割（extract='ai'），
AI 输出结构化 JSON 后入库（ai_parse.py insert）。
"""
DEFAULT_SITE = {
    'key': 'default',
    'name': '大厂通用',
    'type': 'company',
    'list_urls': [
        'https://jobs.bytedance.com/campus/position',
        'https://join.qq.com/post.html',
        'https://talent.alibaba.com/campus/position-list',
        'https://career.huawei.com/reccampportal/portal5/campus-recruitment.html',
        'https://zhaopin.meituan.com/web/campus',
        'https://job.xiaohongshu.com/campus',
    ],
    'link_pattern': None,
    'link_limit': 400,
    'detail_limit': 400,
    # 整页爬取后交 AI 分割
    'extract': 'ai',
    'ai_split': True,
}
