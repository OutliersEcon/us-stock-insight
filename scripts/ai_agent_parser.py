"""
ai_agent_parser.py — 真實財報數據更新腳本
===========================================

職責
----
找出 last_updated 超過指定天數的企業，
實際從 SEC EDGAR 抓取最新財報文字，
再交由 AI 分析結構化，並更新 data/processed/companies.json。

可由 Manus Scheduled Task 定期呼叫，也可由用家主動執行。

工作流程（兩階段）
------------------
Phase 1 — 抓取真實財報：
    1. 從 SEC EDGAR company_tickers.json 查詢 CIK（官方 JSON API，不需要 HTML 解析）
    2. 透過 data.sec.gov/submissions/CIK{cik}.json 取得最新 10-Q / 10-K 申報連結
    3. 下載申報文件的純文字內容
    4. 記錄所有實際訪問的 URL 作為 sources

Phase 2 — AI 分析與結構化：
    將真實抓取的財報文字交給 AI 分析，
    提取業務板塊佔比並生成繁體中文描述。
    AI 僅作為「文字理解與結構化」工具，
    不允許 AI 自行捏造數字或來源 URL。

來源優先順序
------------
1. SEC EDGAR 最新 10-Q（季報）
2. SEC EDGAR 最新 10-K（年報）
3. 若以上均無法取得，標記 data_quality: "estimated"，
   並使用 SEC EDGAR 搜尋頁面作為 sources（此 URL 永遠有效）

使用方式
--------
    # 更新所有超過 30 天未更新的企業（預設）
    python3 scripts/ai_agent_parser.py

    # 指定閾值（天數）
    python3 scripts/ai_agent_parser.py --stale-days 14

    # 強制更新指定企業（忽略 last_updated）
    python3 scripts/ai_agent_parser.py --force AAPL MSFT NVDA

    # 預覽哪些企業需要更新（不執行）
    python3 scripts/ai_agent_parser.py --dry-run

    # 更新後自動重新生成 HTML 頁面
    python3 scripts/ai_agent_parser.py --regenerate-pages

    # 限制單次更新數量（節省 API 費用）
    python3 scripts/ai_agent_parser.py --max-companies 10

API 金鑰設定
------------
本腳本使用環境變數 MANUS_API_KEY 作為 OpenAI 相容 API 的金鑰。
請在 GitHub 倉庫的 Settings → Secrets and variables → Actions 中設定此 Secret，
切勿將金鑰明碼寫入程式碼或提交至版本控制。
"""

import json
import os
import sys
import time
import argparse
import re
import subprocess
from datetime import date
from pathlib import Path

import requests
from openai import OpenAI

# ─────────────────────────────────────────────────────────────────────────────
# 設定
# ─────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
COMPANIES_FILE = REPO_ROOT / "data" / "processed" / "companies.json"
UPDATE_LOG_FILE = REPO_ROOT / "data" / "update_log.json"

DEFAULT_STALE_DAYS = 30

# SEC EDGAR 要求 User-Agent 必須包含 email 地址，否則回傳 403
# 注意：github.io 域名的 email 會被 SEC 封鎖，需要使用普通 .com 域名
SEC_HEADERS = {
    "User-Agent": "us-stock-insight admin@outliersecon.com"
}

# 非美國上市企業（不在 SEC EDGAR），跳過 SEC 查詢
NON_SEC_TICKERS = {"TSM", "FUTU"}


# ─────────────────────────────────────────────────────────────────────────────
# SEC EDGAR 工具函數
# ─────────────────────────────────────────────────────────────────────────────

def get_cik_from_ticker(ticker: str) -> str | None:
    """
    從 SEC EDGAR 查詢 Ticker 對應的 CIK 號碼。

    使用 efts.sec.gov Full-Text Search API，可在沙盒環境正常訪問。
    www.sec.gov 的 company_tickers.json 在部分環境（如 Manus 沙盒）會回傳 403，
    但 efts.sec.gov 不受此限制。

    查詢邏輯：
    1. 搜尋 ticker 字串在 10-Q 申報中的出現
    2. 從 entity_filter aggregation 中找出 ticker 完全匹配的企業
    3. 若無完全匹配，回傳 None
    """
    ticker_upper = ticker.upper()
    url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker_upper}%22&forms=10-Q"
    try:
        resp = requests.get(url, headers=SEC_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        buckets = data.get("aggregations", {}).get("entity_filter", {}).get("buckets", [])

        # 優先找 ticker 完全匹配的企業（格式："COMPANY NAME  (TICKER)  (CIK XXXXXXXXXX)"）
        for bucket in buckets:
            display_name = bucket.get("key", "")
            # 檢查 ticker 是否出現在括號中（精確匹配）
            if f"({ticker_upper})" in display_name or f"({ticker_upper}," in display_name:
                cik_match = re.search(r"CIK (\d+)", display_name)
                if cik_match:
                    return cik_match.group(1).zfill(10)

        # 若 10-Q 無結果，嘗試 10-K
        url_10k = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker_upper}%22&forms=10-K"
        resp2 = requests.get(url_10k, headers=SEC_HEADERS, timeout=15)
        resp2.raise_for_status()
        data2 = resp2.json()
        buckets2 = data2.get("aggregations", {}).get("entity_filter", {}).get("buckets", [])
        for bucket in buckets2:
            display_name = bucket.get("key", "")
            if f"({ticker_upper})" in display_name or f"({ticker_upper}," in display_name:
                cik_match = re.search(r"CIK (\d+)", display_name)
                if cik_match:
                    return cik_match.group(1).zfill(10)

    except Exception as e:
        print(f"    [WARN] CIK lookup failed for {ticker}: {e}")
    return None


def get_latest_filing(cik: str, form_type: str = "10-Q") -> dict | None:
    """
    從 SEC EDGAR 取得指定企業最新的 10-Q 或 10-K 申報資訊。
    回傳 {"filing_url", "search_url", "period", "filed_date", "form_type"} 或 None。
    """
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        resp = requests.get(url, headers=SEC_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        accessions = filings.get("accessionNumber", [])
        periods = filings.get("reportDate", [])
        filed_dates = filings.get("filingDate", [])

        for i, form in enumerate(forms):
            if form == form_type:
                accession = accessions[i].replace("-", "")
                period = periods[i] if i < len(periods) else "Unknown"
                filed = filed_dates[i] if i < len(filed_dates) else "Unknown"
                cik_int = int(cik)
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/"
                search_url = (
                    f"https://www.sec.gov/cgi-bin/browse-edgar"
                    f"?action=getcompany&CIK={cik_int}&type={form_type}"
                    f"&dateb=&owner=include&count=5"
                )
                return {
                    "filing_url": filing_url,
                    "search_url": search_url,
                    "period": period,
                    "filed_date": filed,
                    "form_type": form_type,
                    "cik": cik
                }
    except Exception as e:
        print(f"    [WARN] Filing lookup failed for CIK {cik}: {e}")
    return None


def fetch_filing_text(filing_url: str, max_chars: int = 8000) -> str:
    """
    從 SEC EDGAR 申報頁面抓取主要文件的純文字內容。
    優先選取 .htm 主文件，移除 HTML 標籤後截取前 max_chars 字元。
    """
    try:
        index_url = filing_url + "index.json"
        resp = requests.get(index_url, headers=SEC_HEADERS, timeout=15)
        resp.raise_for_status()
        index_data = resp.json()
        files = index_data.get("directory", {}).get("item", [])

        main_doc = None
        for f in files:
            name = f.get("name", "").lower()
            if name.endswith(".htm") and not name.startswith("r") and "ex" not in name:
                main_doc = filing_url + f["name"]
                break

        if not main_doc:
            return ""

        doc_resp = requests.get(main_doc, headers=SEC_HEADERS, timeout=20)
        text = re.sub(r"<[^>]+>", " ", doc_resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]

    except Exception as e:
        print(f"    [WARN] Filing text fetch failed: {e}")
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# AI 分析函數
# ─────────────────────────────────────────────────────────────────────────────

def analyze_with_ai(company: dict, filing_text: str,
                    filing_info: dict | None, client: OpenAI) -> dict | None:
    """
    將真實財報文字交給 AI 分析，提取業務板塊佔比並生成繁體中文描述。
    AI 僅作為「文字理解與結構化」工具，不允許捏造數字或來源 URL。
    """
    ticker = company["ticker"]
    name = company.get("name", ticker)
    sector = company.get("sector", "Unknown")
    period_label = filing_info["period"] if filing_info else "Unknown"
    form_type = filing_info["form_type"] if filing_info else "10-K"

    if filing_text:
        context = (
            f"以下是 {ticker} ({name}) 的 SEC {form_type} 申報文字節錄"
            f"（申報期間：{period_label}）：\n\n{filing_text}\n\n"
            f"請根據以上真實財報文字進行分析。"
        )
        data_quality_hint = "real_data"
    else:
        context = (
            f"無法取得 {ticker} ({name}) 的財報文字。\n"
            f"請根據你對此公司的知識進行分析，"
            f"並在 data_period 中標注「估計值，未能取得最新財報」，"
            f"data_quality 填 estimated。"
        )
        data_quality_hint = "estimated"

    prompt = f"""{context}

公司行業：{sector}

請以 JSON 格式回傳以下資訊（只回傳 JSON，不要加任何說明文字）：

{{
  "description": "用繁體中文（2-3句）描述公司的核心業務，說明主要產品/服務及市場定位",
  "revenue_segments": [
    {{"segment": "業務板塊名稱（英文）", "percentage": 45, "description": "簡短說明（繁體中文）"}},
    ...
  ],
  "data_period": "財報期間，例如 FY2027 Q1（截至 2026 年 4 月 26 日）",
  "data_quality": "{data_quality_hint}"
}}

規則：
- revenue_segments 按 percentage 由大到小排列
- 所有 percentage 加總必須等於 100
- description 使用繁體中文
- segment 名稱使用英文
- 只回傳 JSON，不要加任何說明文字"""

    try:
        response = client.chat.completions.create(
            model="claude-sonnet-4-6",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.1
        )
        content = response.choices[0].message.content if response.choices else None
        if not content:
            return None

        json_match = re.search(r'\{[\s\S]*\}', content)
        if not json_match:
            return None

        result = json.loads(json_match.group())

        # 驗證必要欄位
        if "description" not in result or "revenue_segments" not in result:
            return None

        # 確保百分比加總接近 100
        total = sum(s.get("percentage", 0) for s in result["revenue_segments"])
        if abs(total - 100) > 5 and result["revenue_segments"]:
            diff = 100 - sum(s["percentage"] for s in result["revenue_segments"][:-1])
            result["revenue_segments"][-1]["percentage"] = max(1, diff)

        # 確保板塊按百分比降冪排序
        result["revenue_segments"] = sorted(
            result["revenue_segments"],
            key=lambda s: s.get("percentage", 0),
            reverse=True
        )

        return result

    except Exception as e:
        print(f"    [ERROR] AI analysis failed for {ticker}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 主要更新邏輯
# ─────────────────────────────────────────────────────────────────────────────

def get_stale_companies(companies: list, stale_days: int,
                        force_tickers: list = None) -> list:
    """找出需要更新的企業清單，按 last_updated 升冪排列（最舊的優先）。"""
    today = date.today()
    stale = []

    for c in companies:
        ticker = c["ticker"]
        if force_tickers and ticker in force_tickers:
            stale.append(c)
            continue
        last_updated_str = c.get("last_updated", "2000-01-01")
        try:
            last_updated = date.fromisoformat(last_updated_str)
            if (today - last_updated).days >= stale_days:
                stale.append(c)
        except ValueError:
            stale.append(c)

    stale.sort(key=lambda c: c.get("last_updated", "2000-01-01"))
    return stale


def update_company(company: dict, client: OpenAI) -> dict | None:
    """
    更新單間企業的財報數據。
    Phase 1: 從 SEC EDGAR 抓取真實財報文字與來源 URL。
    Phase 2: 交由 AI 分析結構化。
    回傳更新後的 company dict，或 None（若更新失敗）。
    """
    ticker = company["ticker"]
    name = company.get("name", ticker)

    sources = []
    filing_info = None
    filing_text = ""

    # ── Phase 1: SEC EDGAR 查詢
    if ticker not in NON_SEC_TICKERS:
        print(f"    → Querying SEC EDGAR for CIK...")
        cik = get_cik_from_ticker(ticker)
        time.sleep(0.3)

        if cik:
            print(f"    → CIK found: {int(cik)}")
            for form_type in ["10-Q", "10-K"]:
                filing_info = get_latest_filing(cik, form_type)
                time.sleep(0.5)
                if filing_info:
                    print(f"    → Found {form_type}: period={filing_info['period']}, filed={filing_info['filed_date']}")
                    # 加入 SEC EDGAR 搜尋頁面（永遠有效的 URL）
                    sources.append({
                        "title": f"SEC EDGAR {form_type} Filings — {name}",
                        "url": filing_info["search_url"]
                    })
                    # 嘗試抓取申報文字
                    filing_text = fetch_filing_text(filing_info["filing_url"])
                    time.sleep(1.0)
                    if filing_text:
                        print(f"    → Fetched {len(filing_text)} chars from filing document")
                        sources.append({
                            "title": f"{name} {form_type} ({filing_info['period']}) — SEC EDGAR",
                            "url": filing_info["filing_url"]
                        })
                    break
        else:
            print(f"    → CIK not found on SEC EDGAR")
            sources.append({
                "title": f"SEC EDGAR — {name}",
                "url": (
                    f"https://www.sec.gov/cgi-bin/browse-edgar"
                    f"?action=getcompany&CIK={ticker}&type=10-K"
                    f"&dateb=&owner=include&count=5"
                )
            })
    else:
        print(f"    → Non-SEC company, skipping EDGAR lookup")
        sources.append({
            "title": f"{name} — Investor Relations",
            "url": f"https://www.google.com/search?q={ticker}+investor+relations+annual+report"
        })

    # ── Phase 2: AI 分析
    print(f"    → Running AI analysis (data_quality: {'real_data' if filing_text else 'estimated'})...")
    ai_result = analyze_with_ai(company, filing_text, filing_info, client)

    if not ai_result:
        print(f"    → [FAIL] AI analysis returned no result")
        return None

    data_quality = ai_result.get("data_quality", "estimated")
    data_period = ai_result.get("data_period", "")
    print(f"    → data_quality={data_quality}, period={data_period}")
    print(f"    → segments: {[s['segment'] for s in ai_result['revenue_segments']]}")

    # 組合更新後的 company dict
    updated = dict(company)
    updated["description"] = ai_result["description"]
    updated["revenue_segments"] = ai_result["revenue_segments"]
    updated["data_period"] = data_period
    updated["data_quality"] = data_quality
    updated["sources"] = sources
    updated["last_updated"] = date.today().isoformat()

    return updated


# ─────────────────────────────────────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Update stale company financial data from real SEC EDGAR sources + AI analysis.\n"
            "Can be run manually or as a Manus Scheduled Task."
        )
    )
    parser.add_argument(
        "--stale-days", type=int, default=DEFAULT_STALE_DAYS,
        help=f"Update companies not updated in this many days (default: {DEFAULT_STALE_DAYS})"
    )
    parser.add_argument(
        "--force", nargs="+", metavar="TICKER",
        help="Force update specific tickers regardless of last_updated"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show which companies would be updated without actually updating"
    )
    parser.add_argument(
        "--regenerate-pages", action="store_true",
        help="After updating, regenerate update_log.json and all HTML pages"
    )
    parser.add_argument(
        "--max-companies", type=int, default=None,
        help="Limit the number of companies to update in one run"
    )
    args = parser.parse_args()

    today = date.today().isoformat()
    print(f"\n{'='*60}")
    print(f"  us-stock-insight — Financial Data Updater")
    print(f"  Date: {today}")
    print(f"{'='*60}\n")

    # 載入 companies.json
    with open(COMPANIES_FILE, encoding="utf-8") as f:
        companies = json.load(f)

    # 找出需要更新的企業
    force_tickers = [t.upper() for t in args.force] if args.force else None
    stale = get_stale_companies(companies, args.stale_days, force_tickers)

    if args.max_companies:
        stale = stale[:args.max_companies]

    print(f"  Total companies: {len(companies)}")
    print(f"  Stale threshold: {args.stale_days} days")
    print(f"  Companies to update: {len(stale)}")
    if stale:
        print(f"  Tickers: {', '.join(c['ticker'] for c in stale)}")
    print()

    if args.dry_run:
        print("DRY RUN — no changes will be made.\n")
        for c in stale:
            try:
                days = (date.today() - date.fromisoformat(c.get("last_updated", "2000-01-01"))).days
            except ValueError:
                days = "?"
            print(f"  {c['ticker']:8s}  last_updated={c.get('last_updated', 'N/A')}  ({days} days ago)")
        return

    if not stale:
        print("✅ All companies are up to date. Nothing to update.")
        return

    # 初始化 OpenAI client
    api_key = os.environ.get("MANUS_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: MANUS_API_KEY or OPENAI_API_KEY environment variable not set.")
        sys.exit(1)

    api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    client = OpenAI(api_key=api_key, base_url=api_base)

    # 建立 ticker → company 的映射（保留原始順序）
    companies_map = {c["ticker"]: c for c in companies}
    companies_order = [c["ticker"] for c in companies]
    success_count = 0
    fail_count = 0

    for i, company in enumerate(stale, 1):
        ticker = company["ticker"]
        print(f"[{i}/{len(stale)}] Updating {ticker} ({company.get('name', ticker)})...")

        updated = update_company(company, client)

        if updated:
            companies_map[ticker] = updated
            success_count += 1
            print(f"    ✅ {ticker} updated successfully\n")
        else:
            fail_count += 1
            print(f"    ❌ {ticker} update failed, keeping existing data\n")

        # 每 5 間儲存一次進度，避免中途失敗損失所有進度
        if i % 5 == 0:
            ordered = [companies_map[t] for t in companies_order]
            with open(COMPANIES_FILE, "w", encoding="utf-8") as f:
                json.dump(ordered, f, ensure_ascii=False, indent=2)
            print(f"  💾 Progress saved ({i}/{len(stale)} processed)\n")

        time.sleep(1.5)  # 避免 API rate limit

    # 最終儲存
    ordered = [companies_map[t] for t in companies_order]
    with open(COMPANIES_FILE, "w", encoding="utf-8") as f:
        json.dump(ordered, f, ensure_ascii=False, indent=2)

    print(f"{'='*60}")
    print(f"  Update complete!")
    print(f"  ✅ Success: {success_count}")
    print(f"  ❌ Failed:  {fail_count}")
    print(f"  💾 Saved to: {COMPANIES_FILE}")
    print(f"{'='*60}\n")

    # 重新生成 update_log 與 HTML 頁面
    if args.regenerate_pages:
        print("Regenerating update_log.json and HTML pages...")
        subprocess.run(
            [sys.executable, "scripts/generate_update_log.py"],
            cwd=REPO_ROOT, check=False
        )
        subprocess.run(
            [sys.executable, "scripts/generate_pages.py"],
            cwd=REPO_ROOT, check=False
        )
        print("✅ Pages regenerated.")


if __name__ == "__main__":
    main()
