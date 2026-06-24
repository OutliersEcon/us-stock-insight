"""
ai_agent_parser.py
==================
使用 AI Agent 自動更新 data/processed/companies.json 中過期企業的業務描述與營收結構。

執行邏輯
--------
1. 讀取 data/update_log.json，找出 needs_update: true 的企業清單。
2. 對每間過期企業，呼叫 AI 生成最新的業務描述、營收佔比、資料時間性與來源。
3. 將更新結果寫回 companies.json，並更新 last_updated 為今天的日期。
4. 若 update_log.json 不存在，則對所有企業執行更新。

資料來源政策（重要）
-------------------
本腳本的 sources 欄位要求 AI 提供其分析所依據的實際財報文件 URL。
AI 必須提供：
  - 公司最新季度或年度財報的直接 URL（SEC EDGAR 10-K/10-Q 文件、公司 IR 頁面）
  - data_period 欄位說明資料的時間性（如 "FY2027 Q1 (截至 2026 年 4 月 26 日)"）
注意：AI 生成的 URL 可能存在幻覺風險。建議定期人工抽查 sources 連結的有效性。
對於重要企業，應優先使用人工更新流程（直接訪問財報並手動填寫 sources）。

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

你的分析必須基於公司最新的官方財報文件，包括：
- SEC EDGAR 申報的 10-K（年報）或 10-Q（季報）
- 公司官方發佈的 Earnings Press Release 或 CFO Commentary
- 公司投資者關係頁面的財務摘要

重要的資料來源政策：
1. sources 欄位必須列出你分析時實際參考的財報文件 URL
2. 優先使用 SEC EDGAR 的直接文件 URL（如 https://www.sec.gov/Archives/edgar/data/...）
3. 或使用公司 IR 頁面的財報下載連結
4. data_period 必須明確說明資料的時間性（如 "FY2027 Q1 (截至 2026 年 4 月 26 日)"）
5. 若無法確認某 URL 的真實性，請使用 SEC EDGAR 的搜尋頁面而非捏造直接連結

回覆必須是嚴格的 JSON 格式，不得包含任何 markdown 標記或額外說明文字。"""

USER_PROMPT_TEMPLATE = """請分析以下公司的業務結構，並以 JSON 格式回覆：

公司名稱：{name}
股票代碼：{ticker}
行業：{sector}

請提供：
1. description：一段 60-100 字的繁體中文業務描述，說明公司的核心業務模式與競爭優勢
2. revenue_segments：各業務板塊的名稱（英文）、營收佔比（整數百分比，合計必須為 100）、繁體中文說明
   - 板塊必須按百分比由大到小排列
3. data_period：資料的時間性說明，格式如 "FY2027 Q1 (截至 2026 年 4 月 26 日)" 或 "FY2026 Annual"
4. sources：2-4 個資料來源，包括：
   - 優先：SEC EDGAR 的 10-K 或 10-Q 申報搜尋頁面（格式：https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K&dateb=&owner=include&count=10）
   - 公司投資者關係頁面（如 https://investor.nvidia.com/）
   - 若有具體財報文件 URL（如 q4cdn.com 的 PDF），請提供
   - 注意：只提供你有信心真實存在的 URL，不確定的請使用 SEC EDGAR 搜尋頁面代替

回覆格式：
{{
  "description": "...",
  "data_period": "FY2027 Q1 (截至 2026 年 X 月 X 日)",
  "revenue_segments": [
    {{"segment": "Segment Name", "percentage": 50, "description": "中文說明"}},
    ...
  ],
  "sources": [
    {{"title": "SEC EDGAR 10-K Filings - {name}", "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K&dateb=&owner=include&count=10"}},
    {{"title": "公司投資者關係頁面", "url": "https://investor.example.com/"}},
    ...
  ]
}}

重要提醒：
- sources 中的 URL 應是你分析時實際參考的來源，不要捏造不存在的 PDF 直接連結
- 若不確定具體 PDF URL，請使用 SEC EDGAR 搜尋頁面（上述格式）
- data_period 必須填寫，說明你的數據來自哪個財報期間"""


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
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        result = json.loads(content)

        # 驗證格式
        if 'description' not in result or 'revenue_segments' not in result:
            print(f"   ⚠️  {company['ticker']} 回傳格式不完整，跳過。")
            return None

        # 確保 data_period 欄位存在
        if 'data_period' not in result or not result['data_period']:
            result['data_period'] = ''
            print(f"   ⚠️  {company['ticker']} 缺少 data_period 欄位。")

        # 驗證 sources 欄位：若缺少則使用 SEC EDGAR 搜尋頁面（真實存在的 URL）
        if 'sources' not in result or not isinstance(result['sources'], list) or len(result['sources']) == 0:
            print(f"   ⚠️  {company['ticker']} 缺少 sources 欄位，使用 SEC EDGAR 搜尋頁面。")
            ticker_val = company['ticker']
            result['sources'] = [
                {
                    "title": f"SEC EDGAR Filings - {company['name']}",
                    "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker_val}&type=10-K&dateb=&owner=include&count=10"
                },
                {
                    "title": f"SEC EDGAR 10-Q Filings - {company['name']}",
                    "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker_val}&type=10-Q&dateb=&owner=include&count=10"
                }
            ]

        # 確保百分比合計為 100
        total = sum(s.get('percentage', 0) for s in result['revenue_segments'])
        if total != 100:
            diff = 100 - total
            result['revenue_segments'][-1]['percentage'] += diff

        # 確保板塊按百分比降冪排序
        result['revenue_segments'] = sorted(
            result['revenue_segments'],
            key=lambda x: x.get('percentage', 0),
            reverse=True
        )

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
    print("⚠️  注意：AI 生成的 sources URL 可能存在幻覺風險。")
    print("   對於重要企業，建議人工驗證 sources 連結的有效性。")
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
            company['sources'] = result.get('sources', company.get('sources', []))
            company['data_period'] = result.get('data_period', '')
            company['last_updated'] = TODAY
            updated_count += 1
            period_info = f"，資料期間：{company['data_period']}" if company['data_period'] else ''
            print(f"   ✓ 更新成功（{len(result['revenue_segments'])} 個業務板塊，{len(company['sources'])} 個來源{period_info}）")
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
    print(f"   已更新：{updated_count} 間企業")
    print(f"   已跳過：{skipped_count} 間企業（資料仍在有效期內）")
    print()
    print("📌 提醒：請人工抽查 sources 連結的有效性，特別是新更新的企業。")


if __name__ == '__main__':
    main()
