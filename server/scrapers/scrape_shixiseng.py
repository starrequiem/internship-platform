"""
实习僧 — 列表页收集详情链接 → 详情页 SSR 抓取（详情页内容清晰，无字体混淆）

列表页: https://www.shixiseng.com/interns
详情页: https://www.shixiseng.com/intern/inn_XXXX

用法: python scrape_shixiseng.py [--max 100]
"""
import json
import os
import sys
import io
import re
import time
import argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from playwright.sync_api import sync_playwright
from extract import split_detail, deadline_from_apply_time
from config import CITIES, extract_company_fallback, classify_job_type
from inserter import insert_item, get_conn

LIST_URL = 'https://www.shixiseng.com/interns'
DETAIL = 'https://www.shixiseng.com/intern/{}'


def collect_links(page, max_items=120):
    """列表页翻页收集详情链接（点数字分页 li.number，去重）"""
    urls = []
    try:
        page.goto(LIST_URL, wait_until='domcontentloaded', timeout=40000)
        page.wait_for_timeout(3000)
        page_num = 0
        while len(urls) < max_items and page_num < 30:
            page_num += 1
            for _ in range(4):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(500)
            batch = page.evaluate('''() => {
                const out = [], seen = new Set();
                document.querySelectorAll('a[href*="/intern/inn_"]').forEach(a => {
                    const href = a.getAttribute('href').split('?')[0];
                    if (href && !seen.has(href)) { seen.add(href); out.push(href); }
                });
                return out;
            }''')
            for u in batch:
                if u not in urls:
                    urls.append(u)
            # 点下一页（active 的下一个数字，或 next 按钮）
            clicked = page.evaluate('''() => {
                const lis = [...document.querySelectorAll('ul li.number')];
                const idx = lis.findIndex(li => li.classList.contains('active'));
                const next = idx >= 0 ? lis[idx + 1] : null;
                if (next) { next.click(); return true; }
                const btn = document.querySelector('.btn-next, [class*="btn-next"]');
                if (btn) { btn.click(); return true; }
                return false;
            }''')
            if not clicked:
                break
            page.wait_for_timeout(2500)
    except Exception as e:
        print(f'  列表抓取失败: {e}')
    return urls[:max_items]


def scrape_detail(page, path):
    """抓取单个详情页，返回结构化 item"""
    slug = path.split('/')[-1]
    url = DETAIL.format(slug)
    result = {
        'title': '', 'company': '', 'city': '全国', 'job_type': '技术开发',
        'salary_min': None, 'salary_max': None, 'education': '本科及以上',
        'days_per_week': 4, 'duration_months': 3, 'deadline': None,
        'description': '', 'requirements': '', 'contact_info': '🔗 原文链接：' + url,
        'url': url,
    }
    try:
        page.goto(result['url'], wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(2500)
        body = page.evaluate('() => document.body ? document.body.innerText : ""') or ''

        # 标题：正文里「刷新」时间行（如「2026-08-17 14:20 刷新」）的前一行
        lines = [l.strip() for l in body.split('\n') if l.strip()]
        title = ''
        for i, l in enumerate(lines):
            if '刷新' in l and i > 0:
                title = lines[i - 1]
                break
        if len(title) < 2:
            title = page.evaluate('''() => { const h = document.querySelector('h1'); return h ? h.innerText.trim() : ''; }''') or ''
        result['title'] = title[:200] or '待识别'

        # 薪资/城市/学历/天数/时长 元信息行，如「120/天 上海 本科 5天／周 实习2个月」
        sal = re.search(r'(\d+)\s*(?:[-~至]\s*(\d+))?\s*元?/天', body)
        if sal:
            result['salary_min'] = int(sal.group(1))
            result['salary_max'] = int(sal.group(2)) if sal.group(2) else int(sal.group(1))
        for c in CITIES:
            if c in body[:600]:
                result['city'] = c
                break
        if '硕士' in body[:600]: result['education'] = '硕士及以上'
        elif '博士' in body[:600]: result['education'] = '博士'
        elif '大专' in body[:600]: result['education'] = '大专'
        dm = re.search(r'(\d+)\s*天\s*[/／]\s*周', body)
        if dm: result['days_per_week'] = int(dm.group(1))
        dur = re.search(r'实习\s*(\d+)\s*个?月', body)
        if dur: result['duration_months'] = int(dur.group(1))

        # 公司（「公司简介」下一行）
        m = re.search(r'公司简介\s*\n\s*([^\n]{2,40})', body)
        if m:
            result['company'] = m.group(1).strip()
        else:
            result['company'] = extract_company_fallback(body) or '待识别'

        # 职位描述 / 任职要求
        desc, req = split_detail(body)
        result['description'] = desc[:5000]
        result['requirements'] = req[:3000]

        # 截止日期
        dl = re.search(r'截止日期\s*[:：]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})', body)
        if dl:
            result['deadline'] = deadline_from_apply_time(dl.group(1))

        # 岗位类型（标题关键词兜底）
        result['job_type'] = classify_job_type(result['title'])
    except Exception as e:
        print(f'  详情抓取异常: {str(e)[:60]}')
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--max', type=int, default=100)
    args = ap.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})
        print('第1步：收集列表链接')
        urls = collect_links(page, args.max)
        print(f'共 {len(urls)} 个详情链接')

        print('第2步：抓取详情页')
        items = []
        for i, u in enumerate(urls):
            it = scrape_detail(page, u)
            items.append(it)
            print(f'  [{i+1}/{len(urls)}] {it["title"][:24]} | {it["company"][:14]} | {it["city"]} | desc:{len(it["description"])} req:{len(it["requirements"])}')
            time.sleep(0.5)
        browser.close()

    conn = get_conn()
    ins = skip = 0
    for it in items:
        try:
            if insert_item(it): ins += 1
            else: skip += 1
        except Exception:
            skip += 1
    print(f'\n入库: 新增 {ins} | 跳过 {skip}')


if __name__ == '__main__':
    main()
