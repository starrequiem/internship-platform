"""
统一爬虫 — 按站点配置抓取，结构化提取或 AI 分割，导出 CSV + 直接入库

用法:
  python scraper.py                    # 爬牛客网（默认），导出 CSV + 直接入库
  python scraper.py --site default     # 爬大厂通用（整页 -> AI 分割）
  python scraper.py --clear            # 先清空旧实习数据再入库
  python scraper.py --export-only      # 只抓取导出 CSV，不入库
  python scraper.py --dry-run          # 只抓取不保存（测试用）
"""
import json
import os
import sys
import io
import re
import time
import csv
import argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from playwright.sync_api import sync_playwright
from config import COMPANIES, CITIES, extract_company_fallback, clean_company
from extract import split_detail, extract_apply_time, deadline_from_apply_time
from sites import get_site, ALL_SITES
from inserter import insert_item, get_conn

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, '..', 'scraped_data')
EXPORT_DIR = os.path.join(DATA_DIR, 'export')
os.makedirs(EXPORT_DIR, exist_ok=True)

CANONICAL_HEADERS = [
    '岗位名称', '公司名称', '工作城市', '岗位类型', '详细地址',
    '最低薪资', '最高薪资', '学历要求', '每周出勤', '实习时长',
    '面向年级', '面向专业', '招聘人数', '截止日期', '投递时间',
    '职位描述', '任职要求', '联系信息', '标签',
]


def collect_links(page, site):
    """收集列表页所有岗位链接（去重）"""
    jobs = []
    if site['type'] == 'aggregator':
        for city in site.get('cities', ['']):
            url = site['list_url']
            if city:
                url += ('&' if '?' in url else '?') + 'city=' + city
            print(f'  列表页 [{city or "全国"}]: {url}')
            jobs += _collect_one_list(page, url, site)
            time.sleep(1.5)
    else:
        for url in site.get('list_urls', []):
            print(f'  列表页: {url}')
            jobs += _collect_one_list(page, url, site)
            time.sleep(1.5)

    seen, uniq = set(), []
    for j in jobs:
        if j['url'] not in seen:
            seen.add(j['url'])
            uniq.append(j)
    return uniq[:site.get('detail_limit', 400)]


def _collect_one_list(page, url, site):
    jobs = []
    try:
        page.goto(url, wait_until='networkidle', timeout=60000)
        pat = site.get('link_pattern') or ''
        page_idx = 0
        while page_idx < 50:  # 分页安全上限
            page_idx += 1
            # 滚动加载当前页
            for _ in range(8):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(600)
            # 收集当前页链接
            batch = page.evaluate('''(pat) => {
                const out = [], seen = new Set();
                document.querySelectorAll('a[href]').forEach(a => {
                    const href = a.getAttribute('href') || '';
                    if (!href) return;
                    const full = href.startsWith('http') ? href : location.origin + href;
                    if (pat && href.indexOf(pat) < 0) return;
                    if (!seen.has(full)) {
                        seen.add(full);
                        out.push({url: full, text: (a.innerText || '').trim()});
                    }
                });
                return out;
            }''', pat)
            jobs += batch
            # 尝试点「下一页」（Element UI 分页：.btn-next），翻到底后 disabled 则停止
            clicked = page.evaluate('''() => {
                const btn = document.querySelector('.el-pagination .btn-next');
                if (!btn || btn.disabled || btn.classList.contains('disabled') || btn.classList.contains('is-disabled')) {
                    return false;
                }
                btn.click();
                return true;
            }''')
            if not clicked:
                break
            page.wait_for_timeout(2500)
    except Exception as e:
        print(f'    列表抓取失败: {e}')
    print(f'    收集 {len(jobs)} 个链接')
    return jobs[:site.get('link_limit', 400)]


def scrape_detail(page, job, site):
    """抓取详情页；structured 用边界分割，ai 存整页"""
    url = job['url']
    result = {
        'title': '', 'company': '', 'city': '', 'job_type': '技术开发',
        'salary_min': None, 'salary_max': None, 'education': '本科及以上',
        'days_per_week': 4, 'duration_months': 3, 'headcount': 1,
        'deadline': None, 'apply_time': '', 'description': '', 'requirements': '', 'tags': [],
        'contact_info': '', 'url': url,
    }
    listing = job.get('text', '')

    # 从列表文本先提取薪资/城市/天数
    sal = re.search(r'(\d+)\s*[-~至]\s*(\d+)\s*元/[天日]', listing)
    if sal:
        result['salary_min'] = int(sal.group(1))
        result['salary_max'] = int(sal.group(2))
    for c in CITIES:
        if c in listing:
            result['city'] = c
            break
    dm = re.search(r'(\d+)\s*天/周', listing)
    if dm:
        result['days_per_week'] = int(dm.group(1))
    dur = re.search(r'(?:最少|至少)?\s*(\d+)\s*(?:个)?月', listing)
    if dur:
        result['duration_months'] = int(dur.group(1))

    result['title'] = listing.split('\n')[0].strip()[:200]

    try:
        page.goto(url, wait_until='domcontentloaded', timeout=25000)
        page.wait_for_timeout(2500)
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        page.wait_for_timeout(800)
        body = page.evaluate('() => document.body ? document.body.innerText : ""') or ''

        # 投递时间：区间原文存入 apply_time，末尾日期解析为 deadline（截止日期）
        result['apply_time'] = extract_apply_time(body)
        if result['apply_time']:
            result['deadline'] = deadline_from_apply_time(result['apply_time'])

        # 标题（优先页面 h1）
        h1 = page.evaluate('''() => {
            const h = document.querySelector('h1');
            return h ? h.innerText.trim() : '';
        }''')
        if h1 and len(h1) > 2:
            result['title'] = h1[:200]

        # 公司：优先页面元素，其次从正文兜底
        company = page.evaluate('''() => {
            const el = document.querySelector('.company-name, .corp-name, [class*="company-name"]');
            return el ? el.innerText.trim().split('\\n')[0] : '';
        }''')
        if company and company not in ('待识别', ''):
            result['company'] = clean_company(company)
        else:
            result['company'] = extract_company_fallback(body) or extract_company_fallback(listing) or '待识别'

        if site['extract'] == 'ai':
            # 默认配置：整页保存，交 AI 分割
            result['description'] = body[:8000]
            result['requirements'] = ''
            result['ai_raw'] = body[:8000]
        else:
            desc, req = split_detail(body)
            result['description'] = (desc or listing)[:5000]
            result['requirements'] = req[:3000]

        # 标签
        tags = page.evaluate('''() => {
            const t = [];
            document.querySelectorAll('.tag-item, .skill-tag, [class*="tag"] span, .label-item, .tech-tag').forEach(el => {
                const txt = el.innerText.trim();
                if (txt && txt.length < 20 && t.indexOf(txt) < 0) t.push(txt);
            });
            return t.slice(0, 8);
        }''')
        result['tags'] = tags

    except Exception as e:
        print(f'    详情抓取异常: {e}')
        result['description'] = listing[:5000]

    result['contact_info'] = '🔗 原文链接：' + url

    dl = len(result['description'])
    rl = len(result['requirements'])
    print(f'  ✅ {result["title"][:28]} | {result["company"][:14]} | desc:{dl} req:{rl}')
    return result


def export_csv(items, path):
    """把 items 导出为后台可识别的标准 CSV"""
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=CANONICAL_HEADERS)
        w.writeheader()
        for it in items:
            tags = it.get('tags') or []
            if isinstance(tags, str):
                tags = [tags]
            w.writerow({
                '岗位名称': it.get('title', ''),
                '公司名称': it.get('company', ''),
                '工作城市': it.get('city', ''),
                '岗位类型': it.get('job_type', ''),
                '详细地址': it.get('district', ''),
                '最低薪资': it.get('salary_min', ''),
                '最高薪资': it.get('salary_max', ''),
                '学历要求': it.get('education', ''),
                '每周出勤': it.get('days_per_week', ''),
                '实习时长': it.get('duration_months', ''),
                '面向年级': it.get('target_grade', ''),
                '面向专业': it.get('target_major', ''),
                '招聘人数': it.get('headcount', ''),
                '截止日期': it.get('deadline', ''),
                '投递时间': it.get('apply_time', ''),
                '职位描述': it.get('description', ''),
                '任职要求': it.get('requirements', ''),
                '联系信息': it.get('contact_info', ''),
                '标签': '，'.join(str(t) for t in tags),
            })
    print(f'✅ 已导出 {len(items)} 条 → {path}')


def clear_internships(conn):
    """清空旧实习数据（连同标签关联）"""
    cur = conn.cursor()
    cur.execute('DELETE FROM internship_tags')
    cur.execute('DELETE FROM internships')
    conn.commit()
    print('✅ 已清空旧实习数据（internships / internship_tags）')


def run_ai_mode(site):
    """大厂整页抓取：爬整页正文，保存到 raw_pages 供 AI 分割（不收集链接、不抓详情）"""
    raw_dir = os.path.join(DATA_DIR, 'raw_pages')
    os.makedirs(raw_dir, exist_ok=True)
    urls = site.get('list_urls', [])
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})
        for i, url in enumerate(urls):
            print(f'[{i+1}/{len(urls)}] {url}')
            try:
                page.goto(url, wait_until='networkidle', timeout=40000)
                page.wait_for_timeout(3000)
                for _ in range(5):
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    page.wait_for_timeout(1200)
                text = page.evaluate('() => document.body ? document.body.innerText : ""') or ''
                data = {'name': f'{site["key"]}_{i}', 'url': url, 'text': text, 'html_snippet': ''}
                fname = os.path.join(raw_dir, f'{site["key"]}_{i}_{int(time.time())}.json')
                with open(fname, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f'    整页 {len(text)} 字 -> {os.path.basename(fname)}')
            except Exception as e:
                print(f'    失败: {str(e)[:80]}')
            time.sleep(2)
        browser.close()
    print('\n✅ 整页已保存到 raw_pages/')
    print('下一步: python ai_parse.py prepare 生成 AI prompt → AI 分割 → python ai_parse.py insert 入库')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', default='nowcoder', help='站点 key：nowcoder / default')
    parser.add_argument('--clear', action='store_true', help='入库前清空旧数据')
    parser.add_argument('--export-only', action='store_true', help='只导出 CSV 不入库')
    parser.add_argument('--dry-run', action='store_true', help='只抓取不保存')
    args = parser.parse_args()

    site = get_site(args.site)
    print(f'═══ 站点: {site["name"]} ({site["type"]}) 模式: {site["extract"]} ═══')

    if site.get('extract') == 'ai':
        run_ai_mode(site)
        return

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})

        print('\n第1步：收集列表链接')
        jobs = collect_links(page, site)
        print(f'共 {len(jobs)} 个唯一链接')

        print('\n第2步：抓取详情页')
        limit = min(len(jobs), site.get('detail_limit', 400))
        for i, job in enumerate(jobs[:limit]):
            print(f'[{i+1}/{limit}]', end=' ')
            results.append(scrape_detail(page, job, site))
            time.sleep(1.0)
        browser.close()

    # 保存原始 JSON
    stamp = int(time.time())
    raw_path = os.path.join(DATA_DIR, 'full_jobs', f'{site["key"]}_{stamp}.json')
    os.makedirs(os.path.dirname(raw_path), exist_ok=True)
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump({'items': results, 'count': len(results)}, f, ensure_ascii=False, indent=2)
    print(f'\n✅ 原始数据: {raw_path}')

    if args.dry_run:
        print('--dry-run：跳过导出与入库')
        return

    # 导出 CSV（供后台导入）
    csv_path = os.path.join(EXPORT_DIR, f'{site["key"]}.csv')
    export_csv(results, csv_path)

    if args.export_only:
        print('--export-only：跳过入库')
        return

    # 入库
    print('\n第3步：入库')
    conn = get_conn()
    if args.clear:
        clear_internships(conn)
    inserted = skipped = 0
    for it in results:
        try:
            rid = insert_item(it)
            if rid:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            print(f'  ✖ {it.get("title","?")[:20]}: {e}')
            skipped += 1
    print(f'\n入库完成：新增 {inserted} | 跳过 {skipped}')
    print(f'CSV 可用后台「批量导入」或 export_and_push.py --push 再次导入')


if __name__ == '__main__':
    main()
