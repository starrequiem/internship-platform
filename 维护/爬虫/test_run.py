"""试运行: 抓取1个站点验证流程"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SITES
from fetcher import fetch_site

# 选第一个 dynamic 站点测试
s = SITES[0]  # 华为校招
print(f'[TRIAL] Testing: {s["name"]}')
print(f'        URL: {s["url"]}')
print(f'        Mode: {s["fetcher"]}')

result = fetch_site(s)

print(f'\n--- Result ---')
print(f'Status: {result["status"]}')
print(f'Items: {len(result.get("items", []))}')
print(f'Raw text: {len(result.get("raw_text", ""))} chars')
if result.get('error'):
    print(f'Error: {result["error"]}')
else:
    print('No errors - ready for full crawl!')
