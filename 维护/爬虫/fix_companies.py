"""
公司名修复 — 从原始页面文本中提取公司名，更新数据库
将 raw_pages/ 中的完整页面文本 + 待识别岗位列表合并，
生成 AI prompt 文件供 AI 分析
"""
import json, os, sys, io, glob, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

PROMPT_DIR = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'prompts')
RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'scraped_data', 'raw_pages')
os.makedirs(PROMPT_DIR, exist_ok=True)

def generate_company_prompt():
    """生成用于 AI 提取公司名的 prompt"""

    # 收集所有原始页面文本
    all_texts = []
    files = sorted(glob.glob(os.path.join(RAW_DIR, '*.json')))
    for fpath in files:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        all_texts.append(f'=== {data.get("name","")}: {data.get("url","")} ===\n{data.get("text","")[:20000]}')

    combined = '\n\n'.join(all_texts)

    # 获取待识别的岗位
    from inserter import get_conn
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, city, description FROM internships WHERE company IN ('待识别', '') ORDER BY id")
    unknowns = cur.fetchall()
    conn.close()

    unknown_list = []
    for row in unknowns:
        unknown_list.append(f'ID={row[0]} 岗位={row[1]} 城市={row[2] or ""} 描述={row[3] or ""}')

    unknown_text = '\n'.join(unknown_list[:50])

    prompt = f"""# 任务：从招聘网站文本中找出每个岗位对应的公司名

## 规则
1. 公司名通常在岗位标题后面几行出现，格式可能是"XX公司"、"XX科技有限公司"、"XX集团"等
2. 有些公司名出现在「直达官网」前面一行
3. 有些公司名出现在「互联网」「电商」「人工智能」等行业标签前面一行
4. 如果文本中没有明确公司名，填写"未识别"
5. 只输出 JSON

## 待识别岗位（共{len(unknowns)}个，以下是前50个）
{unknown_text}

## 原始页面文本
{combined[:30000]}

## 输出格式
```json
{{"companies": [{{"id": 岗位ID, "company": "公司名"}}]}}
```
"""
    out_path = os.path.join(PROMPT_DIR, 'fix_companies_prompt.txt')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(prompt)

    print(f'Generated: {out_path}')
    print(f'Unknown companies: {len(unknowns)}')
    print(f'Prompt size: {len(prompt)} chars')
    return out_path

if __name__ == '__main__':
    generate_company_prompt()
