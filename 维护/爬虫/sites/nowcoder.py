"""牛客网配置 — 实习信息汇总网站（优先爬取）

牛客网是聚合站，列表页按城市分页，每行是一个岗位链接。
详情页结构：标题/薪资/公司/职位描述/任职要求 混在正文里，
用整页文本按标题边界分割（见 extract.split_detail）。
"""
NOWCODER = {
    'key': 'nowcoder',
    'name': '牛客网',
    'type': 'aggregator',
    'list_url': 'https://www.nowcoder.com/jobs/intern/center?recruitType=2',
    'cities': ['', '北京', '上海', '深圳', '广州', '杭州', '成都', '南京', '武汉', '西安', '苏州'],
    'link_pattern': '/jobs/detail/',
    # 扩大抓取上限，保证数据完整
    'link_limit': 400,
    'detail_limit': 400,
    'extract': 'structured',
    'ai_split': False,
}
