#!/usr/bin/env python3
"""
add_companies.py
================
通用企業新增工具。透過 AI 為指定的 Ticker 清單生成業務描述與營收結構，
並寫入 data/processed/companies.json。

使用方式
--------
# 新增單間企業：
python3 scripts/add_companies.py AAPL

# 新增多間企業：
python3 scripts/add_companies.py IBKR ONDS RCAT IONQ

# 從 CSV 檔案讀取（每行一個 Ticker）：
python3 scripts/add_companies.py --file tickers.txt

# 強制覆蓋已存在的企業資料：
python3 scripts/add_companies.py --overwrite AAPL MSFT

# 指定企業為 S&P 500 成員（預設為非 S&P 500）：
python3 scripts/add_companies.py --sp500 NEWSTOCK

選項說明
--------
--overwrite     若企業已存在，強制重新生成並覆蓋（預設：跳過已存在的企業）
--sp500         將新增企業標記為 S&P 500 成員（預設：False，即自選企業）
--file PATH     從指定文字檔讀取 Ticker 清單（每行一個 Ticker，支援 # 開頭的注釋行）
--dry-run       僅顯示將處理的 Ticker，不實際執行
--model NAME    指定 AI 模型（預設：claude-sonnet-4-6）

注意事項
--------
- 本腳本使用環境變數 OPENAI_API_KEY（或 MANUS_API_KEY）作為 API 金鑰。
- 新增後請執行 generate_update_log.py 和 generate_pages.py 以更新網站。
- Nasdaq 100 成員資格與 QQQ/SPY 權重請執行 sync_index_data.py 更新。
"""

import argparse
import json
import os
import sys
import time
from datetime import date
from openai import OpenAI

# ── 路徑設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMPANIES_FILE = os.path.join(BASE_DIR, '..', 'data', 'processed', 'companies.json')
TODAY = date.today().isoformat()

# ── API 設定
API_KEY = os.environ.get('MANUS_API_KEY') or os.environ.get('OPENAI_API_KEY')
API_BASE = os.environ.get('OPENAI_API_BASE', 'https://api.openai.com/v1')

# ── 行業分類對照表（可持續擴充）
SECTOR_MAP = {
    "NVDA": "Technology", "AAPL": "Technology", "MSFT": "Technology",
    "AMZN": "Consumer Discretionary", "GOOGL": "Communication Services",
    "GOOG": "Communication Services", "AVGO": "Technology",
    "TSLA": "Consumer Discretionary", "META": "Communication Services",
    "BRK-B": "Financials", "LLY": "Healthcare", "WMT": "Consumer Staples",
    "JPM": "Financials", "AMD": "Technology", "INTC": "Technology",
    "V": "Financials", "XOM": "Energy", "JNJ": "Healthcare",
    "ORCL": "Technology", "LRCX": "Technology", "AMAT": "Technology",
    "CSCO": "Technology", "CAT": "Industrials", "MA": "Financials",
    "COST": "Consumer Staples", "ABBV": "Healthcare", "BAC": "Financials",
    "UNH": "Healthcare", "GE": "Industrials", "MS": "Financials",
    "CVX": "Energy", "KO": "Consumer Staples", "PG": "Consumer Staples",
    "KLAC": "Technology", "HD": "Consumer Discretionary", "GS": "Financials",
    "NFLX": "Communication Services", "TXN": "Technology", "MRK": "Healthcare",
    "PLTR": "Technology", "PM": "Consumer Staples", "DELL": "Technology",
    "WFC": "Financials", "IBM": "Technology", "MRVL": "Technology",
    "C": "Financials", "RTX": "Industrials", "LIN": "Materials",
    "WDC": "Technology", "PANW": "Technology", "AXP": "Financials",
    "QCOM": "Technology", "ANET": "Technology", "ADI": "Technology",
    "APH": "Technology", "TMUS": "Communication Services",
    "PEP": "Consumer Staples", "MCD": "Consumer Discretionary",
    "VZ": "Communication Services", "AMGN": "Healthcare",
    "TJX": "Consumer Discretionary", "NEE": "Utilities",
    "DIS": "Communication Services", "BA": "Industrials", "TMO": "Healthcare",
    "CRWD": "Technology", "GLW": "Technology", "ETN": "Industrials",
    "BLK": "Financials", "DE": "Industrials", "SCHW": "Financials",
    "APP": "Technology", "T": "Communication Services", "UNP": "Industrials",
    "GILD": "Healthcare", "ABT": "Healthcare", "WELL": "Real Estate",
    "BX": "Financials", "UBER": "Technology", "HON": "Industrials",
    "ISRG": "Healthcare", "PFE": "Healthcare", "COP": "Energy",
    "PLD": "Real Estate", "VRT": "Technology", "BKNG": "Consumer Discretionary",
    "CVS": "Healthcare", "CB": "Financials", "DHR": "Healthcare",
    "COF": "Financials", "CRM": "Technology", "PGR": "Financials",
    "SPGI": "Financials", "LOW": "Consumer Discretionary", "VRTX": "Healthcare",
    "MO": "Consumer Staples", "SYK": "Healthcare", "SBUX": "Consumer Discretionary",
    "LMT": "Industrials", "BMY": "Healthcare", "CDNS": "Technology",
    "FTNT": "Technology", "NOW": "Technology", "SNPS": "Technology",
    "ADP": "Technology", "ADBE": "Technology", "ACN": "Technology",
    "CMCSA": "Communication Services", "NXPI": "Technology", "INTU": "Technology",
    "TSM": "Technology", "FUTU": "Financials", "IBKR": "Financials",
    "ONDS": "Technology", "RCAT": "Industrials", "IONQ": "Technology",
    "UMAC": "Industrials",
    "SPCX": "Financials",
    "QBTS": "Technology",
    "RGTI": "Technology",
}

# ── Nasdaq 100 成員集合
NASDAQ100 = {
    "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "AVGO", "TSLA", "META",
    "WMT", "AMD", "COST", "NFLX", "INTC", "CSCO", "TXN", "QCOM", "AMGN",
    "INTU", "ISRG", "ADI", "AMAT", "LRCX", "PANW", "SNPS", "CDNS", "MRVL",
    "KLAC", "CRWD", "FTNT", "TMUS", "VRTX", "GILD", "SBUX", "ADBE", "NXPI",
    "BKNG", "APP", "CMCSA", "ADP", "HON", "PEP", "LIN", "WDC",
}

PROMPT_TEMPLATE = """You are a financial analyst. Provide structured data for the following US-listed company.

Company: {name} (Ticker: {ticker})
Sector: {sector}

Return ONLY a valid JSON object with these exact fields:
{{
  "description": "<繁體中文，2-3句，描述公司核心業務模式與競爭優勢，60-100字>",
  "revenue_segments": [
    {{"segment": "<英文業務板塊名稱>", "percentage": <整數佔比>, "description": "<繁體中文說明，20-40字>"}},
    ...
  ]
}}

Rules:
- description must be in Traditional Chinese (繁體中文)
- revenue_segments descriptions must be in Traditional Chinese (繁體中文)
- segment names should be in English
- percentages must be integers and sum to exactly 100
- sort revenue_segments by percentage descending (largest first)
- provide 2-6 segments based on actual business structure
- use the most recent fiscal year data available
- return ONLY the JSON object, no markdown, no code blocks, no explanation
"""


def load_companies() -> list:
    """載入 companies.json，若不存在則回傳空清單。"""
    if not os.path.exists(COMPANIES_FILE):
        print(f"⚠️  找不到 {COMPANIES_FILE}，將建立新檔案。")
        return []
    with open(COMPANIES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_companies(companies: list) -> None:
    """儲存 companies.json。"""
    os.makedirs(os.path.dirname(COMPANIES_FILE), exist_ok=True)
    with open(COMPANIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)


def generate_company_data(client, ticker: str, name: str, sector: str, model: str) -> dict | None:
    """呼叫 AI API 生成企業資料，失敗時最多重試 3 次。"""
    prompt = PROMPT_TEMPLATE.format(ticker=ticker, name=name, sector=sector)

    for attempt in range(1, 4):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3,
            )
            content = response.choices[0].message.content
            if not content or not content.strip():
                print(f"   ⚠️  第 {attempt} 次嘗試：回傳空白內容")
                continue

            # 去除可能的 markdown code block
            content = content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            content = content.strip()

            data = json.loads(content)

            # 驗證必要欄位
            if 'description' not in data or 'revenue_segments' not in data:
                print(f"   ⚠️  第 {attempt} 次嘗試：回傳格式不完整")
                continue

            # 確保百分比合計為 100
            total = sum(s.get('percentage', 0) for s in data['revenue_segments'])
            if total != 100:
                diff = 100 - total
                data['revenue_segments'][-1]['percentage'] += diff

            # 按百分比降冪排序
            data['revenue_segments'].sort(key=lambda x: x['percentage'], reverse=True)

            return data

        except json.JSONDecodeError as e:
            print(f"   ⚠️  第 {attempt} 次嘗試：JSON 解析失敗 — {e}")
        except Exception as e:
            print(f"   ⚠️  第 {attempt} 次嘗試：API 錯誤 — {e}")
            time.sleep(2)

    return None


def infer_sector(ticker: str) -> str:
    """從 SECTOR_MAP 推斷行業，找不到時回傳 Unknown 並提示使用者。"""
    sector = SECTOR_MAP.get(ticker.upper())
    if not sector:
        print(f"   ℹ️  {ticker} 不在 SECTOR_MAP 中，行業設為 'Unknown'。")
        print(f"      請在 scripts/add_companies.py 的 SECTOR_MAP 中手動加入 \"{ticker}\": \"<Sector>\"。")
        return "Unknown"
    return sector


def parse_args():
    parser = argparse.ArgumentParser(
        description="為指定的 Ticker 清單生成 AI 企業資料並加入 companies.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python3 scripts/add_companies.py IBKR ONDS RCAT
  python3 scripts/add_companies.py --overwrite AAPL
  python3 scripts/add_companies.py --sp500 NEWSTOCK
  python3 scripts/add_companies.py --file tickers.txt
  python3 scripts/add_companies.py --dry-run TSLA NVDA
        """
    )
    parser.add_argument('tickers', nargs='*', help='要新增的 Ticker 代號（可多個）')
    parser.add_argument('--file', '-f', metavar='PATH',
                        help='從文字檔讀取 Ticker 清單（每行一個，# 開頭為注釋）')
    parser.add_argument('--overwrite', action='store_true',
                        help='若企業已存在，強制重新生成並覆蓋')
    parser.add_argument('--sp500', action='store_true',
                        help='將新增企業標記為 S&P 500 成員（預設：False）')
    parser.add_argument('--dry-run', action='store_true',
                        help='僅顯示將處理的 Ticker，不實際執行')
    parser.add_argument('--model', default='claude-sonnet-4-6',
                        help='指定 AI 模型（預設：claude-sonnet-4-6）')
    return parser.parse_args()


def main():
    args = parse_args()

    # 收集 Ticker 清單
    tickers = [t.upper() for t in args.tickers]

    if args.file:
        if not os.path.exists(args.file):
            print(f"❌ 找不到檔案：{args.file}")
            sys.exit(1)
        with open(args.file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    tickers.append(line.upper())

    if not tickers:
        print("❌ 請提供至少一個 Ticker 代號。")
        print("   用法：python3 scripts/add_companies.py TICKER1 TICKER2 ...")
        sys.exit(1)

    # 去重並保持順序
    seen = set()
    tickers = [t for t in tickers if not (t in seen or seen.add(t))]

    print(f"📋 待處理 Ticker：{', '.join(tickers)}")

    if args.dry_run:
        print("（dry-run 模式，不執行實際操作）")
        return

    # 載入現有資料
    companies = load_companies()
    existing = {c['ticker']: i for i, c in enumerate(companies)}

    # 初始化 API client
    if not API_KEY:
        print("❌ 找不到 MANUS_API_KEY 或 OPENAI_API_KEY 環境變數。")
        sys.exit(1)
    client = OpenAI(api_key=API_KEY, base_url=API_BASE)

    added = 0
    overwritten = 0
    skipped = 0
    failed = 0

    for i, ticker in enumerate(tickers, 1):
        print(f"\n[{i}/{len(tickers)}] 處理 {ticker}...")

        # 檢查是否已存在
        if ticker in existing and not args.overwrite:
            print(f"   ⏭️  已存在，跳過（使用 --overwrite 強制更新）")
            skipped += 1
            continue

        # 推斷行業
        sector = infer_sector(ticker)

        # 嘗試從現有資料取得公司名稱
        if ticker in existing:
            name = companies[existing[ticker]]['name']
        else:
            # 使用 Ticker 作為暫定名稱，AI 會根據 Ticker 推斷
            name = ticker

        # 呼叫 AI 生成資料
        data = generate_company_data(client, ticker, name, sector, args.model)

        if not data:
            print(f"   ❌ 無法生成 {ticker} 的資料，跳過。")
            failed += 1
            continue

        entry = {
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "description": data['description'],
            "weight": 0.0,
            "last_updated": TODAY,
            "nasdaq100": ticker in NASDAQ100,
            "revenue_segments": data['revenue_segments'],
            "in_sp500": args.sp500,
            "qqq_weight": 0.0,
        }

        if ticker in existing:
            # 覆蓋時保留原有的 weight、qqq_weight、in_sp500（除非指定 --sp500）
            old = companies[existing[ticker]]
            entry['weight'] = old.get('weight', 0.0)
            entry['qqq_weight'] = old.get('qqq_weight', 0.0)
            if not args.sp500:
                entry['in_sp500'] = old.get('in_sp500', False)
            entry['name'] = old.get('name', ticker)
            companies[existing[ticker]] = entry
            overwritten += 1
            print(f"   ✅ 已覆蓋更新（{len(data['revenue_segments'])} 個業務板塊）")
        else:
            companies.append(entry)
            added += 1
            print(f"   ✅ 已新增（{len(data['revenue_segments'])} 個業務板塊）")
            print(f"      描述：{data['description'][:50]}…")

        # 避免 API rate limit
        if i < len(tickers):
            time.sleep(1)

    # 儲存結果
    save_companies(companies)

    print(f"\n{'='*50}")
    print(f"✅ 完成！")
    print(f"   新增：{added} 間")
    print(f"   覆蓋更新：{overwritten} 間")
    print(f"   跳過（已存在）：{skipped} 間")
    print(f"   失敗：{failed} 間")
    print(f"   總計：{len(companies)} 間企業")
    print(f"\n📌 後續步驟：")
    print(f"   1. python3 scripts/sync_index_data.py   # 更新 SPY/QQQ 權重")
    print(f"   2. python3 scripts/generate_update_log.py")
    print(f"   3. python3 scripts/generate_pages.py")


if __name__ == '__main__':
    main()
