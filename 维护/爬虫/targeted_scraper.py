"""
针对性抓取 - Playwright 动态页面
"""
import json, os, time, sys, io
# 强制 UTF-8 输出，防止 Windows GBK 乱码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'targeted')
os.makedirs(OUT_DIR, exist_ok=True)

def scrape_nowcoder():
    """牛客网 - 提取岗位列表+详情链接"""
    print('\n[NOWCODER] Starting...')
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})

        try:
            page.goto('https://www.nowcoder.com/jobs/intern/center?recruitType=2',
                      wait_until='networkidle', timeout=90000)
            page.wait_for_timeout(10000)

            # 用JS在页面内提取所有带链接的岗位
            job_links = page.evaluate('''() => {
                const results = [];
                const seen = new Set();
                // 找所有包含 jobId 或 /detail 的链接
                document.querySelectorAll('a[href]').forEach(a => {
                    const href = a.getAttribute('href');
                    if (href && (href.includes('jobId') || href.includes('/detail'))) {
                        const text = (a.innerText || '').trim().slice(0, 100);
                        if (!seen.has(href)) {
                            seen.add(href);
                            const url = href.startsWith('http') ? href : 'https://www.nowcoder.com' + href;
                            results.push({title: text, url: url});
                        }
                    }
                });
                return results;
            }''')
            print(f'  Job links found: {len(job_links)}')

            body_text = page.locator('body').inner_text()
            print(f'  Body text: {len(body_text)} chars')

            results.append({
                'site': 'Nowcoder',
                'url': page.url,
                'items': [],
                'raw_text': body_text[:50000],
                'job_links': job_links,
                'status': 'fulltext',
            })

        except Exception as e:
            print(f'  Error: {e}')
            results.append({'site': 'Nowcoder', 'error': str(e), 'status': 'error'})
        finally:
            browser.close()

    fname = os.path.join(OUT_DIR, f'nowcoder_{int(time.time())}.json')
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(results[0], f, ensure_ascii=False, indent=2)
    print(f'  Saved: {fname}')
    return results


def scrape_xybsyw():
    """应届生求职网"""
    print('\n[XYBSYW] Starting...')
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 375, 'height': 812})

        try:
            page.goto('https://m.xybsyw.com/page/student.html',
                      wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(5000)

            body_text = page.locator('body').inner_text()

            # 提取链接
            job_links = page.evaluate('''() => {
                const results = [];
                document.querySelectorAll('a[href]').forEach(a => {
                    const href = a.getAttribute('href');
                    if (href && (href.includes('job') || href.includes('detail') || href.includes('position'))) {
                        results.push({title: (a.innerText||'').trim().slice(0,100), url: href});
                    }
                });
                return results;
            }''')
            print(f'  Job links: {len(job_links)}, Body: {len(body_text)} chars')

            results.append({
                'site': 'XYBSYW',
                'url': page.url,
                'items': [],
                'raw_text': body_text[:50000] or page.content()[:50000],
                'job_links': job_links,
                'status': 'fulltext',
            })
        except Exception as e:
            print(f'  Error: {e}')
            results.append({'site': 'XYBSYW', 'error': str(e), 'status': 'error'})
        finally:
            browser.close()

    fname = os.path.join(OUT_DIR, f'xybsyw_{int(time.time())}.json')
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(results[0], f, ensure_ascii=False, indent=2)
    print(f'  Saved: {fname}')
    return results


if __name__ == '__main__':
    scrape_nowcoder()
    scrape_xybsyw()
