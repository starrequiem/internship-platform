"""站点配置注册表

用法：
  from sites import ALL_SITES          # 全部站点
  from sites import get_site('nowcoder')  # 按 key 取单站

每个站点配置的字段：
  key          站点标识（nowcoder / default）
  name         显示名
  type         aggregator=汇总网站 | company=大厂官网
  list_url     列表页 URL（汇总网站）
  list_urls    列表页 URL 列表（大厂官网）
  cities       汇总网站按城市分页
  link_pattern 详情链接匹配模式（可选）
  link_limit   每个城市/每站收集链接上限
  detail_limit 详情抓取上限
  extract      structured=结构化提取 | ai=整页交 AI 分割
"""
from .nowcoder import NOWCODER
from .default_site import DEFAULT_SITE

ALL_SITES = [NOWCODER, DEFAULT_SITE]
_BY_KEY = {s['key']: s for s in ALL_SITES}


def get_site(key):
    return _BY_KEY.get(key, NOWCODER)
