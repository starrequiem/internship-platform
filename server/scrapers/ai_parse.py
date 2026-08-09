"""
AI 解析辅助 — 将原始页面文本 + AI 提示词合并
输出：可直接发给 AI 的完整 prompt 文件，或 AI 返回的 JSON 数据入库

用法：
  python ai_parse.py prepare    # 生成 AI prompt 文件（raw_pages/*.json → prompts/）
  python ai_parse.py insert     # 将 AI 返回的 JSON 入库（parsed_ai/*.json → MySQL）
"""
import json, os, sys, io, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_DIR = os.path.dirname(__file__)
RAW_DIR = os.path.join(BASE_DIR, '..', 'scraped_data', 'raw_pages')
PROMPT_DIR = os.path.join(BASE_DIR, '..', 'scraped_data', 'prompts')
PARSED_DIR = os.path.join(BASE_DIR, '..', 'scraped_data', 'parsed_ai')
PROMPT_FILE = os.path.join(BASE_DIR, 'AI_PARSE_PROMPT.md')

os.makedirs(PROMPT_DIR, exist_ok=True)
os.makedirs(PARSED_DIR, exist_ok=True)


def cmd_prepare():
    """读取原始文本，合并 AI 提示词，生成可直接发给 AI 的文件"""
    if not os.path.exists(PROMPT_FILE):
        print(f'Error: {PROMPT_FILE} not found')
        return

    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    files = glob.glob(os.path.join(RAW_DIR, '*.json'))
    if not files:
        print('No raw pages found. Run fullpage_scraper.py first.')
        return

    for fpath in files:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        name = data.get('name', 'unknown')
        text = data.get('text', '')
        html_snippet = data.get('html_snippet', '')
        url = data.get('url', '')

        # 合并文本（原始text + html片段中的链接信息）
        combined = f'来源URL: {url}\n\n=== 页面正文 ===\n{text[:80000]}\n\n=== 链接片段 ===\n{html_snippet[:30000]}'

        # 生成完整 prompt
        full_prompt = prompt_template + '\n\n' + combined

        out_name = os.path.join(PROMPT_DIR, f'{name}_prompt.txt')
        with open(out_name, 'w', encoding='utf-8') as f:
            f.write(full_prompt)

        print(f'{name}: {len(combined)} chars → {out_name}')

    print(f'\n生成了 {len(files)} 个 prompt 文件到 {PROMPT_DIR}/')
    print('将这些文件的内容发给 AI，AI 会返回 JSON。')
    print('把 AI 返回的 JSON 保存到 parsed_ai/ 目录，然后运行: python ai_parse.py insert')


def cmd_insert():
    """将 AI 解析的 JSON 入库"""
    sys.path.insert(0, BASE_DIR)
    from inserter import insert_item

    files = glob.glob(os.path.join(PARSED_DIR, '*.json'))
    if not files:
        # 也检查 prompts 目录下是否有 AI 返回的文件
        files = glob.glob(os.path.join(PROMPT_DIR, '*result*.json'))
        files += glob.glob(os.path.join(PROMPT_DIR, '*parsed*.json'))

    if not files:
        print('No AI-parsed JSON files found in parsed_ai/ or prompts/')
        print('Save AI response JSON to parsed_ai/ and try again.')
        return

    total_in, total_skip = 0, 0
    for fpath in files:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        items = data.get('items', [])
        print(f'\n{fpath}: {len(items)} items')

        for item in items:
            try:
                rid = insert_item(item)
                if rid: total_in += 1
                else: total_skip += 1
            except Exception as e:
                print(f'  Error: {item.get("title","?")} — {e}')
                total_skip += 1

    print(f'\n入库: {total_in} 新增 | {total_skip} 跳过')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'prepare'
    if cmd == 'insert':
        cmd_insert()
    else:
        cmd_prepare()
