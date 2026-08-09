"""
爬取引擎  基于 Scrapling
"""
import json, os, sys, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from config import SITES

from scrapling.fetchers import Fetcher, DynamicFetcher, StealthyFetcher

# 输出目录
RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'scraped_data')
os.makedirs(RAW_DIR, exist_ok=True)

def fetch_page(url, mode='static'):
    """
    根据模式抓取页面
    - static: Fetcher.get(url)
    - dynamic: DynamicFetcher.fetch(url)
    - stealthy: StealthyFetcher.fetch(url)
    """
    if mode == 'dynamic':
        return DynamicFetcher.fetch(url)
    elif mode == 'stealthy':
        try:
            return StealthyFetcher.fetch(url)
        except Exception:
            print('[warn] StealthyFetcher unavailable, fallback to DynamicFetcher')
            return DynamicFetcher.fetch(url)
    else:
        return Fetcher.get(url)


def fetch_site(site_config):
    """
    抓取单个站点
    返回: { 'site': str, 'url': str, 'items': [...], 'raw_text': str, 'status': str }
    """
    name = site_config['name']
    url = site_config['url']
    mode = site_config.get('fetcher', 'static')
    selectors = site_config.get('selectors', {})
    parser_type = site_config.get('parser', 'html')

    print(f'\n{"="*60}')
    print(f' {name}: {url}')
    print(f'   Mode: {mode} | Parser: {parser_type}')

    result = {
        'site': name,
        'url': url,
        'items': [],
        'raw_text': '',
        'fetched_at': datetime.now().isoformat(),
        'status': 'pending',
    }

    try:
        page = fetch_page(url, mode)
        text_len = len(page.text or '') if hasattr(page, 'text') else len(str(page))
        print(f'   Page fetched ({text_len} chars)')

        # 提取页面文本
        page_text = page.text or ''
        if not page_text and hasattr(page, 'body'):
            body = page.body
            if isinstance(body, bytes):
                page_text = body.decode('utf-8', errors='replace')
            elif hasattr(body, 'text_content'):
                page_text = body.text_content() or ''
        # 如果还是没有，尝试用CSS提取全文
        if not page_text and hasattr(page, 'css'):
            try:
                page_text = page.css('body::text').getall()
                page_text = ' '.join(page_text) if page_text else ''
            except Exception:
                pass
        page_text = (page_text or '')[:50000]

        # 尝试结构化提取
        if selectors and parser_type == 'html':
            items = extract_items(page, selectors)
            if items:
                result['items'] = items
                result['status'] = 'structured'
                print(f'   Structured: {len(items)} items')
            else:
                result['raw_text'] = page_text
                result['status'] = 'fulltext'
                print(f'   Selector miss, saved fulltext ({len(result["raw_text"])} chars)')
        else:
            result['raw_text'] = page_text
            result['status'] = 'fulltext'
            print(f'   Fulltext saved ({len(result["raw_text"])} chars)')

    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
        print(f'    抓取失败: {e}')

    # 保存原始结果
    safe_name = name.replace('/', '_').replace('\\', '_')
    fname = os.path.join(RAW_DIR, f'{safe_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'    保存到: {fname}')

    return result


def extract_items(page, selectors):
    """用 CSS 选择器从页面提取结构化列表"""
    items = []
    list_sel = selectors.get('list', '')

    if list_sel:
        cards = page.css(list_sel)
        print(f'    列表选择器匹配: {len(cards)} 个元素')
        for card in cards[:50]:  # 最多取50条
            item = {}
            for field in ['title', 'company', 'city', 'job_type', 'salary', 'description']:
                sel = selectors.get(field, '')
                if sel:
                    try:
                        val = card.css(f'{sel}::text').get()
                        if val:
                            item[field] = val.strip()
                    except Exception:
                        pass
            if item.get('title'):  # 至少有标题才算有效
                items.append(item)
    else:
        # 没有列表选择器，尝试通用提取
        for field in ['title', 'company', 'city', 'job_type']:
            sel = selectors.get(field, '')
            if sel:
                try:
                    vals = page.css(f'{sel}::text').getall()
                    print(f'    {field}: 找到 {len(vals)} 个')
                except Exception:
                    pass

    return items


def fetch_all(sites=None):
    """抓取全部站点"""
    if sites is None:
        sites = SITES

    results = []
    for i, site in enumerate(sites):
        print(f'\n[{i+1}/{len(sites)}]')
        result = fetch_site(site)
        results.append(result)
        if i < len(sites) - 1:
            time.sleep(2)  # 礼貌性延迟

    # 汇总
    structured = sum(1 for r in results if r['status'] == 'structured')
    fulltext  = sum(1 for r in results if r['status'] == 'fulltext')
    errors    = sum(1 for r in results if r['status'] == 'error')
    total_items = sum(len(r['items']) for r in results)

    print(f'\n{"="*60}')
    print(f' 抓取汇总: {len(results)} 个站点')
    print(f'    结构化: {structured} |  整页: {fulltext} |  失败: {errors}')
    print(f'    共提取 {total_items} 条实习信息')
    print(f'    原始数据目录: {RAW_DIR}')

    return results


if __name__ == '__main__':
    fetch_all(SITES[:2])  # 测试前两个
