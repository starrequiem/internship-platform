"""
详情页爬虫 — 访问每个岗位的URL，提取完整职位描述、任职要求、公司信息
"""
import json, os, time, sys, io, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'raw_pages')
DETAIL_DIR = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'detail_pages')
os.makedirs(DETAIL_DIR, exist_ok=True)

def scrape_detail(url, job_id):
    """抓取单个岗位详情页"""
    result = {'url': url, 'job_id': job_id, 'description': '', 'requirements': '',
              'company': '', 'city': '', 'title': '', 'error': ''}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})

        try:
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)

            body_text = page.locator('body').inner_text()

            # 提取标题
            try:
                result['title'] = page.locator('h1, .job-title, .position-title, [class*="title"]').first.inner_text().strip()[:200]
            except: pass

            # 提取公司名
            try:
                result['company'] = page.locator('.company-name, .corp-name, [class*="company"], .employer-name').first.inner_text().strip()[:100]
            except: pass

            # 提取所有可见文本（包含职位描述等）
            result['description'] = body_text[:10000]

            # 提取HTML中可能的描述区域
            try:
                desc_selectors = ['.job-desc', '.position-desc', '[class*="desc"]',
                                 '.job-content', '.position-content', '.detail-content',
                                 '.job-detail', 'article', '.job-requirement',
                                 '[class*="requirement"]', '[class*="require"]']
                for sel in desc_selectors:
                    try:
                        desc_text = page.locator(sel).first.inner_text()
                        if len(desc_text) > 50:
                            result['requirements'] = desc_text[:5000]
                            break
                    except: pass
            except: pass

            print(f'  [{job_id}] {result["title"][:40]} | {result["company"][:20]} | desc:{len(result["description"])} req:{len(result["requirements"])}')

        except Exception as e:
            result['error'] = str(e)
            print(f'  [{job_id}] Error: {e}')
        finally:
            browser.close()

    return result

def main():
    # 读取所有 raw_pages 中已解析的URL
    files = sorted(glob.glob(os.path.join(RAW_DIR, '*.json')))
    all_urls = set()

    for fpath in files:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        snippets = data.get('html_snippet', '')
        entries = snippets.split('---\n')
        for entry in entries:
            lines = entry.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('https://www.nowcoder.com/jobs/detail/'):
                    # 提取jobId
                    m = re.search(r'/detail/(\d+)', line)
                    jid = m.group(1) if m else 'unknown'
                    all_urls.add((line, jid))

    print(f'Total unique detail URLs: {len(all_urls)}')

    results = []
    for i, (url, jid) in enumerate(sorted(all_urls)):
        print(f'\n[{i+1}/{len(all_urls)}] {url[:80]}')
        result = scrape_detail(url, jid)
        results.append(result)

        # 保存进度
        if (i+1) % 10 == 0:
            fname = os.path.join(DETAIL_DIR, f'details_batch_{i//10}.json')
            with open(fname, 'w', encoding='utf-8') as f:
                json.dump({'results': results[-10:]}, f, ensure_ascii=False, indent=2)
            print(f'  Saved batch to {fname}')

        time.sleep(1)  # rate limit

    # 最终保存
    fname = os.path.join(DETAIL_DIR, 'all_details.json')
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump({'results': results, 'total': len(results)}, f, ensure_ascii=False, indent=2)
    print(f'\nSaved all {len(results)} details to {fname}')

if __name__ == '__main__':
    main()
