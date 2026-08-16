"""
API 探测 — 加载各站岗位列表页，拦截 XHR/JSON 响应，找出岗位数据 API
用法: python probe_apis.py
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright

SITES = {
    '腾讯': 'https://join.qq.com/post.html',
    '阿里巴巴': 'https://talent.alibaba.com/campus/position-list',
    '华为': 'https://career.huawei.com/reccampportal/portal5/campus-recruitment.html',
    '美团': 'https://zhaopin.meituan.com/web/campus',
    '小红书': 'https://job.xiaohongshu.com/campus',
}

KEYWORDS = ['api', 'list', 'position', 'job', 'recruit', 'campus', 'query', 'search', 'post', 'career']


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})
        for name, url in SITES.items():
            print(f'\n════ {name}: {url} ════')
            calls = []

            def on_response(resp):
                ct = resp.headers.get('content-type', '') or ''
                if 'json' not in ct and 'xml' not in ct:
                    return
                u = resp.url
                if any(k in u.lower() for k in KEYWORDS):
                    calls.append(u)

            page.on('response', on_response)
            try:
                page.goto(url, wait_until='networkidle', timeout=30000)
                page.wait_for_timeout(3000)
                for _ in range(4):
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    page.wait_for_timeout(1200)
            except Exception as e:
                print(f'  加载异常: {str(e)[:60]}')
            page.remove_listener('response', on_response)

            uniq = list(dict.fromkeys(calls))
            print(f'  疑似 API（{len(uniq)} 个）：')
            for u in uniq[:12]:
                print(f'   - {u[:160]}')
        browser.close()


if __name__ == '__main__':
    main()
