"""
爬虫数据 → 后台联动
把 parsed JSON 转成标准 CSV，并可推送到后台导入接口入库。

用法:
  python export_and_push.py            # 导出 CSV 到 scraped_data/export/internships.csv
  python export_and_push.py --push     # 导出并推送到后台导入接口

后台配置可用环境变量覆盖:
  BACKEND_URL     默认 http://localhost:3000
  ADMIN_USER      默认 admin
  ADMIN_PASSWORD  默认 admin123
"""
import os
import sys
import json
import csv
import io
import glob

# 修复 Windows GBK 控制台打印 emoji 报错
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

# 后台导入接口认可的标准表头（与后端 HEADER_MAP 一致）
CANONICAL_HEADERS = [
    '岗位名称', '公司名称', '工作城市', '岗位类型', '详细地址',
    '最低薪资', '最高薪资', '学历要求', '每周出勤', '实习时长',
    '面向年级', '面向专业', '招聘人数', '截止日期', '投递时间',
    '职位描述', '任职要求', '联系信息', '标签',
]

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:3000')
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASSWORD', 'admin123')


def parse_items():
    parsed_dir = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'parsed')
    items = []
    if os.path.isdir(parsed_dir):
        for fname in sorted(glob.glob(os.path.join(parsed_dir, '*.json'))):
            with open(fname, encoding='utf-8') as f:
                data = json.load(f)
            its = data.get('items', []) if isinstance(data, dict) else data
            items.extend(its)
    return items


def item_to_row(it):
    def g(*keys):
        for k in keys:
            v = it.get(k)
            if v not in (None, ''):
                return v
        return ''

    contact = g('contact_info')
    if not contact:
        url = g('source_url', 'url', 'apply_url')
        if url:
            contact = '🔗 原文链接：' + str(url)

    tags = it.get('tags') or []
    if isinstance(tags, str):
        tags = [tags]

    return {
        '岗位名称': g('title'),
        '公司名称': g('company'),
        '工作城市': g('city'),
        '岗位类型': g('job_type'),
        '详细地址': g('district'),
        '最低薪资': g('salary_min'),
        '最高薪资': g('salary_max'),
        '学历要求': g('education'),
        '每周出勤': g('days_per_week'),
        '实习时长': g('duration_months'),
        '面向年级': g('target_grade'),
        '面向专业': g('target_major'),
        '招聘人数': g('headcount'),
        '截止日期': g('deadline'),
        '投递时间': g('apply_time'),
        '职位描述': g('description'),
        '任职要求': g('requirements'),
        '联系信息': contact,
        '标签': '，'.join(str(t) for t in tags),
    }


def build_csv_bytes(items):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CANONICAL_HEADERS)
    w.writeheader()
    for it in items:
        w.writerow(item_to_row(it))
    # utf-8-sig 带 BOM，便于 Excel 正确识别中文
    return buf.getvalue().encode('utf-8-sig')


def main():
    push = '--push' in sys.argv
    items = parse_items()
    if not items:
        print('⚠️ 没有解析数据，请先运行抓取+解析（main.py all 或 fetch.js）')
        return

    csv_bytes = build_csv_bytes(items)
    export_dir = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'export')
    os.makedirs(export_dir, exist_ok=True)
    csv_path = os.path.join(export_dir, 'internships.csv')
    with open(csv_path, 'wb') as f:
        f.write(csv_bytes)
    print(f'✅ 已导出 {len(items)} 条 → {csv_path}')

    if not push:
        print('💡 提示：加 --push 参数可直接推送到后台导入接口')
        return

    import requests
    # 登录后台
    try:
        r = requests.post(BACKEND_URL + '/api/admin/login',
                          json={'username': ADMIN_USER, 'password': ADMIN_PASS}, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f'❌ 无法连接后台（{BACKEND_URL}），请确认后端已启动：{e}')
        return
    token = r.json().get('token')
    if not token:
        print('❌ 后台登录失败:', r.json().get('error'))
        return

    # 上传 CSV 到导入接口
    files = {'file': ('internships.csv', csv_bytes, 'text/csv')}
    resp = requests.post(BACKEND_URL + '/api/admin/internships/import',
                         headers={'Authorization': 'Bearer ' + token}, files=files, timeout=60)
    data = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {}
    if resp.ok:
        print(f"✅ 推送后台成功：插入 {data.get('inserted')} 条，跳过 {data.get('skipped')} 条")
        for e in (data.get('errors') or [])[:10]:
            print('   -', e)
    else:
        print('❌ 推送失败:', data.get('error'))


if __name__ == '__main__':
    main()
