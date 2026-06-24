"""
backfill_sources.py
===================
為 companies.json 中所有缺少 sources 欄位（或 sources 為空陣列）的企業，
使用 AI 批量生成資料來源 URL，並寫回 companies.json。

執行方式：
  python3 scripts/backfill_sources.py
  python3 scripts/backfill_sources.py --overwrite   # 強制重新生成所有企業的 sources
  python3 scripts/backfill_sources.py --ticker AAPL MSFT  # 只處理指定企業
"""

import json
import os
import sys
import time
import argparse
from datetime import date
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMPANIES_FILE = os.path.join(BASE_DIR, '..', 'data', 'processed', 'companies.json')

API_KEY = os.environ.get('MANUS_API_KEY') or os.environ.get('OPENAI_API_KEY')
API_BASE = os.environ.get('OPENAI_API_BASE', 'https://api.openai.com/v1')
MODEL = 'claude-sonnet-4-6'

PROMPT_TEMPLATE = """You are a financial analyst. For the company below, provide ONLY the data sources used for revenue segment analysis.

Company: {name} (Ticker: {ticker})
Sector: {sector}

Return ONLY a valid JSON object:
{{
  "sources": [
    {{"title": "<source name, e.g. Annual Report 10-K FY2024>", "url": "<actual publicly accessible URL>"}},
    ...
  ]
}}

Rules:
- Provide 2-4 real, verifiable source URLs
- MUST include the SEC EDGAR 10-K filing page: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K
- Include the company's investor relations page if it exists (e.g. https://investor.apple.com/)
- Include official annual report or earnings release page if available
- All URLs must be real and publicly accessible — do NOT invent URLs
- Return ONLY the JSON object, no markdown, no explanation
"""


def load_companies():
    with open(COMPANIES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_companies(companies):
    with open(COMPANIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)


def generate_sources(client, ticker, name, sector):
    """呼叫 AI 生成 sources，失敗時最多重試 3 次。"""
    prompt = PROMPT_TEMPLATE.format(ticker=ticker, name=name, sector=sector)

    for attempt in range(1, 4):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.1,
            )
            content = response.choices[0].message.content
            if not content or not content.strip():
                print(f"   ⚠️  第{attempt}次：回傳空白")
                continue

            content = content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            content = content.strip()

            data = json.loads(content)
            sources = data.get('sources', [])

            if not sources or not isinstance(sources, list):
                print(f"   ⚠️  第{attempt}次：sources 格式錯誤")
                continue

            # 確保至少有 SEC EDGAR 連結
            has_sec = any('sec.gov' in s.get('url', '') for s in sources)
            if not has_sec:
                sources.insert(0, {
                    "title": f"SEC EDGAR Filings ({ticker})",
                    "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K"
                })

            return sources

        except json.JSONDecodeError as e:
            print(f"   ⚠️  第{attempt}次：JSON 解析失敗 — {e}")
        except Exception as e:
            print(f"   ⚠️  第{attempt}次：API 錯誤 — {e}")
            time.sleep(2)

    # 全部失敗：回傳預設 SEC EDGAR 連結
    return [
        {
            "title": f"SEC EDGAR Filings ({ticker})",
            "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K"
        }
    ]


def main():
    parser = argparse.ArgumentParser(description="批量補充 companies.json 中的 sources 欄位")
    parser.add_argument('--overwrite', action='store_true', help='強制重新生成所有企業的 sources')
    parser.add_argument('--ticker', nargs='+', metavar='TICKER', help='只處理指定的 Ticker')
    args = parser.parse_args()

    if not API_KEY:
        print("❌ 找不到 MANUS_API_KEY 或 OPENAI_API_KEY 環境變數。")
        sys.exit(1)

    client = OpenAI(api_key=API_KEY, base_url=API_BASE)
    companies = load_companies()

    # 決定要處理的企業
    if args.ticker:
        target_tickers = set(t.upper() for t in args.ticker)
        to_process = [c for c in companies if c['ticker'] in target_tickers]
    elif args.overwrite:
        to_process = companies
    else:
        # 只處理缺少 sources 或 sources 為空的企業
        to_process = [c for c in companies if not c.get('sources')]

    print(f"📋 需要補充 sources 的企業：{len(to_process)} 間")
    if not to_process:
        print("✅ 所有企業均已有 sources 欄位，無需補充。")
        return

    updated = 0
    failed = 0

    for i, company in enumerate(to_process, 1):
        ticker = company['ticker']
        name = company['name']
        sector = company['sector']
        print(f"[{i:03d}/{len(to_process)}] {ticker} ({name})...")

        sources = generate_sources(client, ticker, name, sector)

        # 找到對應的企業並更新
        for c in companies:
            if c['ticker'] == ticker:
                c['sources'] = sources
                break

        print(f"   ✅ {len(sources)} 個來源")
        updated += 1

        if i < len(to_process):
            time.sleep(0.8)

    save_companies(companies)
    print(f"\n✅ 完成！已補充 {updated} 間企業的 sources 欄位。")
    print(f"   失敗：{failed} 間（已以 SEC EDGAR 預設連結代替）")


if __name__ == '__main__':
    main()
