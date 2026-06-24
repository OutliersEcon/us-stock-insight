"""
add_non_index_companies.py
為所有現有企業加入 in_sp500 欄位，並新增 TSM、UMAC、FUTU 三間非指數企業。
"""
import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "processed" / "companies.json"

# 三間新增的非指數企業資料
NEW_COMPANIES = [
    {
        "ticker": "TSM",
        "name": "Taiwan Semiconductor Manufacturing Company",
        "sector": "Technology",
        "description": "全球最大的晶圓代工廠，為 Apple、NVIDIA、AMD 等科技巨頭生產最先進的半導體晶片，掌握全球尖端製程的絕大多數產能。",
        "weight": 0.0,
        "last_updated": "2026-06-24",
        "nasdaq100": False,
        "in_sp500": False,
        "revenue_segments": [
            {"segment": "Advanced Process (≤7nm)", "percentage": 69, "description": "3nm、5nm、7nm 等先進製程，主要客戶為 Apple 及 AI 晶片廠商"},
            {"segment": "Specialty Technology", "percentage": 20, "description": "成熟製程，用於汽車、IoT、工業等應用"},
            {"segment": "Other", "percentage": 11, "description": "封裝測試及其他服務"}
        ]
    },
    {
        "ticker": "UMAC",
        "name": "Unusual Machines",
        "sector": "Industrials",
        "description": "美國本土無人機（Drone）製造商，專注於生產符合美國國防部 Blue UAS 認證的商用與軍用無人機，致力於減少美國對中國無人機供應鏈的依賴。",
        "weight": 0.0,
        "last_updated": "2026-06-24",
        "nasdaq100": False,
        "in_sp500": False,
        "revenue_segments": [
            {"segment": "Drone Hardware", "percentage": 72, "description": "FPV 無人機機體及零組件銷售"},
            {"segment": "Components & Parts", "percentage": 20, "description": "馬達、電調等無人機零件零售"},
            {"segment": "Software & Services", "percentage": 8, "description": "飛控軟體及技術支援服務"}
        ]
    },
    {
        "ticker": "FUTU",
        "name": "Futu Holdings",
        "sector": "Financials",
        "description": "香港及東南亞領先的互聯網券商，旗下擁有富途牛牛（Futubull）及 moomoo 兩大交易平台，為散戶提供港美股、期權及加密貨幣交易服務。",
        "weight": 0.0,
        "last_updated": "2026-06-24",
        "nasdaq100": False,
        "in_sp500": False,
        "revenue_segments": [
            {"segment": "Brokerage Commission", "percentage": 52, "description": "港美股及期權交易佣金收入"},
            {"segment": "Interest Income", "percentage": 36, "description": "融資融券及現金管理利息收入"},
            {"segment": "Wealth Management", "percentage": 8, "description": "基金銷售及理財產品分銷"},
            {"segment": "Other", "percentage": 4, "description": "企業服務及其他收入"}
        ]
    }
]

def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        companies = json.load(f)

    # 1. 為所有現有企業加入 in_sp500 = True（若尚未有此欄位）
    existing_tickers = set()
    for c in companies:
        if "in_sp500" not in c:
            c["in_sp500"] = True
        existing_tickers.add(c["ticker"])

    # 2. 新增三間非指數企業（若尚未存在）
    added = 0
    for nc in NEW_COMPANIES:
        if nc["ticker"] not in existing_tickers:
            companies.append(nc)
            added += 1
            print(f"  ✓ 新增：{nc['ticker']} - {nc['name']}")
        else:
            # 更新現有資料（確保 in_sp500 正確）
            for c in companies:
                if c["ticker"] == nc["ticker"]:
                    c["in_sp500"] = nc["in_sp500"]
                    c["nasdaq100"] = nc["nasdaq100"]
                    print(f"  ↺ 更新：{nc['ticker']} (in_sp500={nc['in_sp500']})")

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完成！企業總數：{len(companies)}（新增 {added} 間）")
    non_sp500 = [c["ticker"] for c in companies if not c.get("in_sp500", True)]
    print(f"   非 S&P 500 企業：{non_sp500}")

if __name__ == "__main__":
    main()
