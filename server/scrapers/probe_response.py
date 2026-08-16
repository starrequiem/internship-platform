"""
API 响应结构探测 — 拦截岗位 API 的响应体，打印 JSON 结构，用于写解析器
用法: python probe_response.py
"""
import sys
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright


def run(name, url, match_kw):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        captured = {}

        def on_response(resp):
            u = resp.url
            if match_kw in u:
                try:
                    body = resp.text()
                    if len(body) > 500 and not captured.get('url'):
                        captured['url'] = u
                        captured['status'] = resp.status
                        captured['body'] = body[:3000]
                except Exception:
                    pass

        page.on('response', on_response)
        try:
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(4000)
            for _ in range(3):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
        except Exception as e:
            print(f'  {name} 加载异常: {str(e)[:60]}')
        browser.close()

        print(f'\n════ {name} ════')
        if captured.get('url'):
            print(f'  API: {captured["url"][:150]}')
            print(f'  status: {captured["status"]}')
            print('  body 前 2500 字:')
            print(captured['body'][:2500])
        else:
            print(f'  未拦截到 {match_kw} 响应（可能需交互触发）')


def main():
    run('腾讯', 'https://join.qq.com/post.html', 'searchPosition')
    run('华为', 'https://career.huawei.com/reccampportal/portal5/campus-recruitment.html', 'getJob')
    run('美团', 'https://zhaopin.meituan.com/web/campus', 'api/official/job')


if __name__ == '__main__':
    main()
