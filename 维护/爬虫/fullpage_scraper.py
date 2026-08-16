"""
全页抓取 — 不解析，只保存原始文本供 AI 解析
抓取牛客网、Boss直聘、实习僧等招聘网站的实习列表页
"""
import json, os, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'raw_pages')
os.makedirs(OUT_DIR, exist_ok=True)

TARGETS = [
    {
        'name': 'nowcoder_intern',
        'url': 'https://www.nowcoder.com/jobs/intern/center?recruitType=2',
        'wait': 10000,
        'scroll': True,
    },
    {
        'name': 'nowcoder_intern_beijing',
        'url': 'https://www.nowcoder.com/jobs/intern/center?recruitType=2&city=北京',
        'wait': 10000,
        'scroll': True,
    },
    {
        'name': 'nowcoder_intern_shanghai',
        'url': 'https://www.nowcoder.com/jobs/intern/center?recruitType=2&city=上海',
        'wait': 10000,
        'scroll': True,
    },
    {
        'name': 'nowcoder_intern_shenzhen',
        'url': 'https://www.nowcoder.com/jobs/intern/center?recruitType=2&city=深圳',
        'wait': 10000,
        'scroll': True,
    },
    {
        'name': 'shixiseng_tech',
        'url': 'https://www.shixiseng.com/interns?k=技术开发&c=北京',
        'wait': 10000,
        'scroll': True,
    },
]

def scrape_page(name, url, wait_ms=10000, do_scroll=True):
    """抓取单个页面，保存完整文本"""
    print(f'\n[{name}] {url}')
    result = {'name': name, 'url': url, 'text': '', 'html_snippet': ''}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})

        try:
            page.goto(url, wait_until='networkidle', timeout=90000)
            page.wait_for_timeout(wait_ms)

            # 滚动加载更多
            if do_scroll:
                for i in range(5):
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    page.wait_for_timeout(2000)

            # 提取全部可见文本
            body_text = page.locator('body').inner_text()

            # 提取关键 HTML 片段（包含链接）
            html_snippets = page.evaluate('''() => {
                const items = [];
                document.querySelectorAll('a[href]').forEach(a => {
                    const href = a.getAttribute('href');
                    const text = (a.innerText || '').trim();
                    if (text.length > 10 && (href.includes('job') || href.includes('detail') || href.includes('position') || href.includes('intern'))) {
                        items.push(text + '\\n' + (href.startsWith('http') ? href : 'https://www.nowcoder.com' + href));
                    }
                });
                return items.join('\\n---\\n');
            }''')

            result['text'] = body_text[:100000]
            result['html_snippet'] = html_snippets[:50000]
            print(f'  Text: {len(result["text"])} chars, Snippets: {len(result["html_snippet"])} chars')

        except Exception as e:
            result['error'] = str(e)
            print(f'  Error: {e}')
        finally:
            browser.close()

    # 保存
    fname = os.path.join(OUT_DIR, f'{name}_{int(time.time())}.json')
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'  Saved: {fname}')
    return result

def main():
    results = []
    for t in TARGETS:
        r = scrape_page(t['name'], t['url'], t['wait'], t.get('scroll', True))
        results.append(r)
        time.sleep(3)

    print(f'\n抓取完成：{len(results)} 个页面')
    print(f'原始文本保存在：{OUT_DIR}')

if __name__ == '__main__':
    main()
