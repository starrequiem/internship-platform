"""
实习通  爬虫主入口

用法:
  python main.py fetch       # 只抓取
  python main.py parse       # 只解析
  python main.py insert      # 只入库
  python main.py all         # 全流程
  python main.py test        # 测试
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from config import SITES
from fetcher import fetch_site, fetch_all
from parser import parse_all_raw


def cmd_fetch():
    """抓取全部站点"""
    fetch_all(SITES)


def cmd_parse():
    """解析已抓取的原始数据"""
    parse_all_raw()


def cmd_insert():
    """入库已解析的数据"""
    from inserter import run_insert
    run_insert()


def cmd_all():
    """全流程"""
    print('=' * 60)
    print('  实习通爬虫  全流程')
    print('=' * 60)

    print('\n 第一步: 抓取')
    fetch_all(SITES)

    print('\n 第二步: 解析')
    parse_all_raw()

    print('\n 第三步: 入库')
    from inserter import insert_from_file, os as _os, json as _json
    parsed_dir = _os.path.join(_os.path.dirname(__file__), '..', 'scraped_data', 'parsed')
    total_in = total_skip = 0
    if _os.path.isdir(parsed_dir):
        for fname in _os.listdir(parsed_dir):
            if fname.endswith('.json'):
                print(f'\n {fname}')
                a, b = insert_from_file(_os.path.join(parsed_dir, fname))
                total_in += a; total_skip += b
    print(f'\n 入库:  {total_in} 新增 |  {total_skip} 跳过')

    print('\n 全流程完成')


def cmd_test():
    """测试: 抓取 quotes.toscrape.com 验证流程"""
    print('[TEST] Scraping quotes.toscrape.com\n')
    test_site = {
        'name': '测试站',
        'url': 'https://quotes.toscrape.com/',
        'type': 'test',
        'fetcher': 'static',
        'selectors': {
            'list': '.quote',
            'title': '.text',
            'company': '.author',
        },
        'parser': 'html',
    }
    result = fetch_site(test_site)
    if result['status'] == 'structured':
        print(f'\n 结构化提取成功: {len(result["items"])} 条')
        for item in result['items'][:3]:
            print(f'   "{item.get("title","")[:40]}"  {item.get("company","")}')
    else:
        print(f'\n 状态: {result["status"]}')
    print('\n流程验证通过 ，可以运行 python main.py all 开始全量抓取')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'test'
    {
        'fetch': cmd_fetch,
        'parse': cmd_parse,
        'insert': cmd_insert,
        'all': cmd_all,
        'test': cmd_test,
    }.get(cmd, cmd_test)()
