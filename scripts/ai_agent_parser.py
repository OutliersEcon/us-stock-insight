"""
ai_agent_parser.py
==================
使用 AI Agent 自動更新 data/processed/companies.json 中過期企業的業務描述與營收結構。

執行邏輯
--------
1. 讀取 data/update_log.json，找出 needs_update: true 的企業清單。
2. 對每間過期企業，呼叫 AI（透過 MANUS_API_KEY）生成最新的業務描述與營收佔比。
3. 將更新結果寫回 companies.json，並更新 last_updated 為今天的日期。
4. 若 update_log.json 不存在，則對所有企業執行更新。

API 金鑰設定
-----------
本腳本使用環境變數 MANUS_API_KEY 作為 OpenAI 相容 API 的金鑰。
請在 GitHub 倉庫的 Settings → Secrets and variables → Actions 中設定此 Secret，
切勿將金鑰明碼寫入程式碼或提交至版本控制。
"""

import json
import os
import sys
import time
from datetime import date
from openai import OpenAI

# ── 路徑設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMPANIES_FILE = os.path.join(BASE_DIR, '..', 'data', 'processed', 'companies.json')
UPDATE_LOG_FILE = os.path.join(BASE_DIR, '..', 'data', 'update_log.json')

# ── API 設定（使用 MANUS_API_KEY）
API_KEY = os.environ.get('MANUS_API_KEY') or os.environ.get('OPENAI_API_KEY')
if not API_KEY:
    print("❌ 錯誤：找不到 MANUS_API_KEY 或 OPENAI_API_KEY 環境變數。")
    print("   請在 GitHub Secrets 中設定 MANUS_API_KEY。")
    sys.exit(1)

# 使用 OpenAI 相容介面（支援 Manus 沙盒環境的 API Base）
API_BASE = os.environ.get('OPENAI_API_BASE', 'https://api.openai.com/v1')
client = OpenAI(api_key=API_KEY, base_url=API_BASE)

TODAY = date.today().isoformat()


SYSTEM_PROMPT = """你是一位專業的財務分析師，專門分析美國上市公司的業務結構與營收組成。
請根據公司最新的年報（10-K）及公開財報資料，提供準確的業務描述與各業務板塊的營收佔比。

回覆必須是嚴格的 JSON 格式，不得包含任何 markdown 標記或額外說明文字。"""

USER_PROMPT_TEMPLATE = """請分析以下公司的業務結構，並以 JSON 格式回覆：

公司名稱：{name}
股票代碼：{ticker}
行業：{sector}

請提供：
1. description：一段 60-100 字的繁體中文業務描述，說明公司的核心業務模式與競爭優勢
2. revenue_segments：各業務板塊的名稱（英文）、營收佔比（整數百分比，合計必須為 100）、繁體中文說明

回覆格式：
{{
  "description": "...",
  "revenue_segments": [
    {{"segment": "Segment Name", "percentage": 50, "description": "中文說明"}},
    ...
  ]
}}"""


def get_stale_tickers() -> list[str]:
    """從 update_log.json 取得需要更新的 ticker 清單。"""
    if not os.path.exists(UPDATE_LOG_FILE):
        print("⚠️  update_log.json 不存在，將更新所有企業。")
        return None  # None 表示更新全部

    with open(UPDATE_LOG_FILE, 'r', encoding='utf-8') as f:
        log = json.load(f)

    stale = [c['ticker'] for c in log['companies'] if c.get('needs_update', True)]
    print(f"📋 update_log.json 讀取完成：{log['total_companies']} 間企業中，{len(stale)} 間需要更新。")
    if stale:
        print(f"   需更新：{', '.join(stale)}")
    return stale


def call_ai(company: dict) -> dict | None:
    """呼叫 AI API 取得公司的最新業務描述與營收結構。"""
    prompt = USER_PROMPT_TEMPLATE.format(
        name=company['name'],
        ticker=company['ticker'],
        sector=company['sector']
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        result = json.loads(content)

        # 驗證格式
        if 'description' not in result or 'revenue_segments' not in result:
            print(f"   ⚠️  {company['ticker']} 回傳格式不完整，跳過。")
            return None

        # 確保百分比合計為 100
        total = sum(s.get('percentage', 0) for s in result['revenue_segments'])
        if total != 100:
            # 調整最後一個板塊以確保合計為 100
            diff = 100 - total
            result['revenue_segments'][-1]['percentage'] += diff

        return result

    except json.JSONDecodeError as e:
        print(f"   ❌ {company['ticker']} JSON 解析失敗：{e}")
        return None
    except Exception as e:
        print(f"   ❌ {company['ticker']} API 呼叫失敗：{e}")
        return None


def main():
    print(f"🤖 AI Agent Parser 啟動 — {TODAY}")
    print(f"   API Base: {API_BASE}")
    print()

    # 讀取 companies.json
    with open(COMPANIES_FILE, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    # 取得需要更新的 ticker 清單
    stale_tickers = get_stale_tickers()

    if stale_tickers is not None and len(stale_tickers) == 0:
        print("✅ 所有企業資料均在有效期內，無需更新。")
        return

    updated_count = 0
    skipped_count = 0

    for i, company in enumerate(companies):
        ticker = company['ticker']

        # 若有指定清單，跳過不在清單中的企業
        if stale_tickers is not None and ticker not in stale_tickers:
            skipped_count += 1
            continue

        print(f"[{i+1:02d}/{len(companies)}] 更新 {ticker} ({company['name']})...")

        result = call_ai(company)
        if result:
            company['description'] = result['description']
            company['revenue_segments'] = result['revenue_segments']
            company['last_updated'] = TODAY
            updated_count += 1
            print(f"   ✓ 更新成功（{len(result['revenue_segments'])} 個業務板塊）")
        else:
            print(f"   ⚠️  更新失敗，保留原有資料。")

        # 避免 API rate limit
        if i < len(companies) - 1:
            time.sleep(1)

    # 寫回 companies.json
    with open(COMPANIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)

    print()
    print(f"✅ AI Agent 更新完成")
    print(f"   已更新：{updated_count} 間")
    print(f"   已跳過（近期已更新）：{skipped_count} 間")
    print(f"   結果已寫回 companies.json")


if __name__ == '__main__':
    main()
