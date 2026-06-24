"""
generate_update_log.py
======================
從 data/processed/companies.json 自動生成 data/update_log.json。

此腳本由 GitHub Actions 在每次 AI 更新資料後自動執行，確保 update_log.json
的內容完全來自 companies.json 的實際數據，不含任何人工填寫或 AI 幻覺。

update_log.json 的用途
-----------------------
AI Agent 在執行更新任務前，應先讀取此檔案，比對 last_updated 日期，
跳過近期（例如 30 天內）已更新的企業，集中資源更新長時間未更新的資料，
以節省 API Token 並提升更新效率。

update_log.json 格式
---------------------
{
  "generated_at": "2025-06-24T10:00:00Z",       // 本次生成時間 (UTC ISO 8601)
  "total_companies": 30,                          // 已收錄企業總數
  "companies": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "last_updated": "2025-06-24",               // YYYY-MM-DD
      "days_since_update": 0,                     // 距今天數（整數）
      "in_sp500": true,                          // 是否為 S&P 500 成分股
      "nasdaq100": true,
      "sector": "Technology",
      "needs_update": false                       // 超過 STALE_DAYS 則為 true
    },
    ...
  ]
}
"""

import json
import os
from datetime import date, datetime, timezone

# ── 設定：超過幾天視為需要更新
STALE_DAYS = 30

COMPANIES_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'companies.json')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'update_log.json')


def main():
    today = date.today()
    now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    with open(COMPANIES_FILE, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    log_entries = []
    stale_count = 0

    for c in companies:
        ticker = c['ticker']
        last_updated_str = c.get('last_updated', '')

        if last_updated_str:
            last_updated_date = date.fromisoformat(last_updated_str)
            days_since = (today - last_updated_date).days
        else:
            last_updated_str = 'N/A'
            days_since = 9999

        needs_update = days_since >= STALE_DAYS
        if needs_update:
            stale_count += 1

        log_entries.append({
            "ticker": ticker,
            "name": c.get('name', ''),
            "last_updated": last_updated_str,
            "days_since_update": days_since,
            "in_sp500": c.get('in_sp500', True),
            "nasdaq100": c.get('nasdaq100', False),
            "sector": c.get('sector', ''),
            "needs_update": needs_update
        })

    # 依 days_since_update 降冪排序（最久未更新的排最前面，方便 AI 優先處理）
    log_entries.sort(key=lambda x: x['days_since_update'], reverse=True)

    output = {
        "generated_at": now_utc,
        "stale_threshold_days": STALE_DAYS,
        "total_companies": len(log_entries),
        "stale_count": stale_count,
        "up_to_date_count": len(log_entries) - stale_count,
        "companies": log_entries
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ update_log.json 已生成")
    print(f"   生成時間：{now_utc}")
    print(f"   企業總數：{len(log_entries)}")
    print(f"   需要更新（>{STALE_DAYS} 天）：{stale_count} 間")
    print(f"   已是最新（<{STALE_DAYS} 天）：{len(log_entries) - stale_count} 間")

    if stale_count > 0:
        print(f"\n   最久未更新的企業：")
        for entry in log_entries[:5]:
            if entry['needs_update']:
                print(f"     {entry['ticker']:10} {entry['last_updated']}  ({entry['days_since_update']} 天前)")


if __name__ == '__main__':
    main()
