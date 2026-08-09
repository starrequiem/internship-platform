"""
针对性抓取 - 用 Playwright 等待 SPA 内容加载后再提取
"""
import json, os, time
from playwright.sync_api import sync_playwright

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'targeted')
os.makedirs(OUT_DIR, exist_ok=True)

def scrape_nowcoder():
    """牛客网 - 等待职位列表加载"""
    print('\n[NOWCODER] Starting...')
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})

        try:
            page.goto('https://www.nowcoder.com/jobs/intern/center?recruitType=2',
                      wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(5000)  # extra wait for dynamic content

            # Try to wait for job cards
            selectors = [
                '.job-list-item', '.recruit-item', '[class*="job"]',
                '[class*="recruit"]', 'li', '.list-item'
            ]
            content = page.content()
            print(f'  Page: {len(content)} chars')

            # Extract all text content
            body_text = page.locator('body').inner_text()
            print(f'  Body text: {len(body_text)} chars')

            # Try to extract job items by looking for patterns
            # Look for company names in the text
            results.append({
                'site': 'Nowcoder',
                'url': page.url,
                'items': [],
                'raw_text': body_text[:50000],
                'status': 'fulltext',
            })

        except Exception as e:
            print(f'  Error: {e}')
            results.append({'site': 'Nowcoder', 'error': str(e), 'status': 'error'})
        finally:
            browser.close()

    # Save
    fname = os.path.join(OUT_DIR, f'nowcoder_{int(time.time())}.json')
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(results[0], f, ensure_ascii=False, indent=2)
    print(f'  Saved: {fname} ({len(results[0].get("raw_text",""))} chars)')
    return results

def scrape_xybsyw():
    """应届生求职网/校友帮"""
    print('\n[XYBSYW] Starting...')
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 375, 'height': 812})  # mobile view

        try:
            page.goto('https://m.xybsyw.com/page/student.html',
                      wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(5000)

            content = page.content()
            body_text = page.locator('body').inner_text()
            print(f'  Page: {len(content)} chars, Body: {len(body_text)} chars')

            results.append({
                'site': 'XYBSYW',
                'url': page.url,
                'items': [],
                'raw_text': body_text[:50000] or content[:50000],
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
    print(f'  Saved: {fname} ({len(results[0].get("raw_text",""))} chars)')
    return results

if __name__ == '__main__':
    scrape_nowcoder()
    scrape_xybsyw()
    print('\nDone!')
