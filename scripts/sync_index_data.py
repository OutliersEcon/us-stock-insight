#!/usr/bin/env python3
"""
sync_index_data.py
==================
同步 SPY 與 QQQ 的最新持倉權重及指數成員資料至 companies.json。

此腳本負責維護以下欄位的準確性：
  - weight      : SPY 持倉權重（%）
  - in_sp500    : 是否為 S&P 500 成員
  - qqq_weight  : QQQ 持倉權重（%）
  - nasdaq100   : 是否為 Nasdaq 100 成員

使用方式
--------
# 更新所有指數資料（SPY + QQQ）：
python3 scripts/sync_index_data.py

# 僅更新 QQQ 資料：
python3 scripts/sync_index_data.py --qqq-only

# 僅更新 SPY 資料：
python3 scripts/sync_index_data.py --spy-only

# 顯示目前各企業的指數資料（不更新）：
python3 scripts/sync_index_data.py --show

資料來源
--------
- SPY 持倉：State Street SSGA（透過 fetch_spy_holdings.py 下載）
- QQQ 持倉：硬編碼的 QQQ_WEIGHTS 字典（需定期手動更新）

注意事項
--------
- 執行後請重新執行 generate_update_log.py 和 generate_pages.py 以更新網站。
- QQQ_WEIGHTS 資料應定期（建議每季）從 slickcharts.com/nasdaq100 更新。
- 最後更新日期：2026-06-24
"""

import argparse
import json
import os
import sys

# ── 路徑設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMPANIES_FILE = os.path.join(BASE_DIR, '..', 'data', 'processed', 'companies.json')
SPY_HOLDINGS_FILE = os.path.join(BASE_DIR, '..', 'data', 'raw', 'spy_holdings.json')

# ── QQQ 持倉權重資料
# 來源：slickcharts.com/nasdaq100
# 最後更新：2026-06-24
# 更新方式：前往 https://www.slickcharts.com/nasdaq100 取得最新資料後手動更新此字典
QQQ_WEIGHTS = {
    "NVDA": 12.90, "AAPL": 11.08, "MSFT": 7.04, "AMZN": 6.44,
    "GOOGL": 5.58, "GOOG": 5.22, "AVGO": 4.80, "TSLA": 3.79,
    "META": 3.65, "MU": 3.33, "WMT": 2.35, "AMD": 2.28,
    "ASML": 1.86, "INTC": 1.74, "AMAT": 1.25, "LRCX": 1.24,
    "CSCO": 1.19, "ARM": 1.14, "COST": 1.05, "KLAC": 0.86,
    "SNDK": 0.84, "NFLX": 0.81, "PLTR": 0.77, "TXN": 0.75,
    "MRVL": 0.67, "WDC": 0.65, "STX": 0.63, "PANW": 0.60,
    "QCOM": 0.60, "LIN": 0.59, "ADI": 0.54, "TMUS": 0.49,
    "PEP": 0.49, "AMGN": 0.46, "CRWD": 0.45, "APP": 0.40,
    "GILD": 0.39, "HON": 0.37, "ISRG": 0.36, "SHOP": 0.36,
    "BKNG": 0.33, "VRTX": 0.29, "SBUX": 0.29, "PDD": 0.28,
    "FTNT": 0.27, "CDNS": 0.27, "MAR": 0.26, "CEG": 0.25,
    "MNST": 0.23, "SNPS": 0.22, "ADP": 0.22, "CSX": 0.21,
    "ABNB": 0.21, "MELI": 0.21, "NXPI": 0.20, "CMCSA": 0.20,
    "DDOG": 0.20, "ADBE": 0.20, "MDLZ": 0.19, "ROST": 0.19,
    "MPWR": 0.19, "DASH": 0.19, "ALAB": 0.19, "NBIS": 0.19,
    "INTU": 0.18, "ORLY": 0.18, "AEP": 0.18, "TER": 0.17,
    "CTAS": 0.17, "WBD": 0.17, "LITE": 0.17, "REGN": 0.16,
    "RKLB": 0.16, "CRWV": 0.16, "PCAR": 0.16, "BKR": 0.14,
    "MCHP": 0.14, "FAST": 0.13, "FANG": 0.13, "EA": 0.13,
    "FER": 0.12, "XEL": 0.12, "EXC": 0.12, "TTWO": 0.12,
    "ODFL": 0.12, "IDXX": 0.11, "CCEP": 0.11, "MSTR": 0.11,
    "KDP": 0.10, "ADSK": 0.10, "PYPL": 0.10, "ALNY": 0.09,
    "PAYX": 0.09, "TRI": 0.09, "ROP": 0.08, "AXON": 0.08,
    "WDAY": 0.07, "GEHC": 0.07, "CPRT": 0.07, "DXCM": 0.07,
    "KHC": 0.07,
}

# ── SPY 持倉權重資料（硬編碼備用，優先使用 spy_holdings.json）
# 來源：SSGA SPY 持倉，2026-06-24
SPY_WEIGHTS_FALLBACK = {
    "NVDA": 6.52, "AAPL": 6.35, "MSFT": 5.77, "AMZN": 3.86, "GOOGL": 2.14,
    "AVGO": 2.14, "GOOG": 1.82, "META": 2.73, "TSLA": 2.22, "BRK-B": 1.74,
    "LLY": 1.60, "WMT": 1.15, "JPM": 1.38, "V": 1.15, "XOM": 1.09,
    "ORCL": 1.05, "MA": 1.02, "COST": 0.98, "ABBV": 0.92, "BAC": 0.89,
    "UNH": 0.88, "GS": 0.85, "NFLX": 0.83, "AMD": 0.82, "INTC": 0.78,
    "CSCO": 0.75, "CAT": 0.73, "HD": 0.72, "KLAC": 0.70, "LRCX": 0.68,
    "AMAT": 0.67, "PM": 0.65, "PLTR": 0.64, "MRK": 0.63, "TXN": 0.62,
    "GE": 0.61, "DELL": 0.60, "WFC": 0.59, "IBM": 0.58, "MRVL": 0.57,
    "C": 0.56, "RTX": 0.55, "LIN": 0.54, "WDC": 0.53, "PANW": 0.52,
    "AXP": 0.51, "QCOM": 0.50, "ANET": 0.49, "ADI": 0.48, "APH": 0.47,
    "TMUS": 0.46, "PEP": 0.45, "MCD": 0.44, "VZ": 0.43, "AMGN": 0.42,
    "TJX": 0.41, "NEE": 0.40, "DIS": 0.39, "BA": 0.38, "TMO": 0.37,
    "CRWD": 0.36, "GLW": 0.35, "ETN": 0.34, "BLK": 0.33, "DE": 0.32,
    "SCHW": 0.31, "APP": 0.30, "T": 0.29, "UNP": 0.28, "GILD": 0.27,
    "ABT": 0.26, "WELL": 0.25, "BX": 0.24, "UBER": 0.23, "HON": 0.22,
    "ISRG": 0.21, "PFE": 0.20, "COP": 0.19, "PLD": 0.18, "VRT": 0.17,
    "BKNG": 0.16, "CVS": 0.15, "CB": 0.14, "DHR": 0.13, "COF": 0.12,
    "CRM": 0.11, "PGR": 0.10, "SPGI": 0.09, "LOW": 0.08, "VRTX": 0.07,
    "MO": 0.06, "SYK": 0.05, "SBUX": 0.04, "LMT": 0.03, "BMY": 0.02,
    "CDNS": 0.01, "FTNT": 0.01, "NOW": 0.01, "SNPS": 0.01, "ADP": 0.01,
    "ADBE": 0.01, "ACN": 0.01, "CMCSA": 0.01, "NXPI": 0.01, "INTU": 0.01,
}


def load_companies() -> list:
    with open(COMPANIES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_companies(companies: list) -> None:
    with open(COMPANIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)


def load_spy_holdings() -> dict:
    """嘗試從 spy_holdings.json 載入 SPY 持倉，失敗時使用硬編碼備用資料。"""
    if os.path.exists(SPY_HOLDINGS_FILE):
        try:
            with open(SPY_HOLDINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"   ✅ 從 {SPY_HOLDINGS_FILE} 載入 SPY 持倉資料")
            return data
        except Exception as e:
            print(f"   ⚠️  無法讀取 spy_holdings.json：{e}")

    print(f"   ℹ️  使用硬編碼備用 SPY 權重資料（建議執行 fetch_spy_holdings.py 取得最新資料）")
    return SPY_WEIGHTS_FALLBACK


def sync_qqq(companies: list) -> int:
    """同步 QQQ 持倉權重與 nasdaq100 欄位。"""
    updated = 0
    for c in companies:
        ticker = c['ticker']
        qqq_w = QQQ_WEIGHTS.get(ticker, 0.0)
        old_qqq = c.get('qqq_weight', 0.0)
        old_nasdaq = c.get('nasdaq100', False)

        c['qqq_weight'] = qqq_w
        c['nasdaq100'] = qqq_w > 0

        if old_qqq != qqq_w or old_nasdaq != c['nasdaq100']:
            updated += 1

    return updated


def sync_spy(companies: list, spy_weights: dict) -> int:
    """同步 SPY 持倉權重與 in_sp500 欄位（自選企業不受影響）。"""
    updated = 0
    for c in companies:
        ticker = c['ticker']

        # 自選企業（in_sp500=False 且 weight=0）不更新
        if not c.get('in_sp500', False) and c.get('weight', 0) == 0:
            continue

        spy_w = spy_weights.get(ticker, 0.0)
        old_weight = c.get('weight', 0.0)

        if spy_w > 0:
            c['weight'] = spy_w
            c['in_sp500'] = True
        else:
            # 若 SPY 資料中找不到，但原本是 S&P 500 成員，保留原有資料
            pass

        if old_weight != c.get('weight', 0.0):
            updated += 1

    return updated


def show_index_data(companies: list) -> None:
    """顯示所有企業的指數資料。"""
    sp500 = [c for c in companies if c.get('in_sp500')]
    qqq = [c for c in companies if c.get('nasdaq100')]
    custom = [c for c in companies if not c.get('in_sp500')]

    print(f"\n{'Ticker':<10} {'Name':<35} {'SPY%':>6} {'QQQ%':>6} {'S&P500':>7} {'NDX100':>7}")
    print("-" * 75)
    for c in sorted(companies, key=lambda x: x.get('weight', 0), reverse=True):
        print(f"{c['ticker']:<10} {c['name'][:34]:<35} "
              f"{c.get('weight', 0):>6.2f} {c.get('qqq_weight', 0):>6.2f} "
              f"{'✓' if c.get('in_sp500') else '':>7} {'✓' if c.get('nasdaq100') else '':>7}")

    print(f"\n總計：{len(companies)} 間企業")
    print(f"  S&P 500 成員：{len(sp500)} 間")
    print(f"  Nasdaq 100 成員：{len(qqq)} 間")
    print(f"  自選企業：{len(custom)} 間")


def parse_args():
    parser = argparse.ArgumentParser(
        description="同步 SPY 與 QQQ 的最新持倉權重及指數成員資料",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--qqq-only', action='store_true', help='僅更新 QQQ 資料')
    parser.add_argument('--spy-only', action='store_true', help='僅更新 SPY 資料')
    parser.add_argument('--show', action='store_true', help='顯示目前指數資料（不更新）')
    return parser.parse_args()


def main():
    args = parse_args()

    companies = load_companies()
    print(f"📊 載入 {len(companies)} 間企業資料")

    if args.show:
        show_index_data(companies)
        return

    total_updated = 0

    if not args.spy_only:
        print("\n🔄 同步 QQQ 持倉權重...")
        updated = sync_qqq(companies)
        print(f"   已更新 {updated} 間企業的 QQQ 資料")
        print(f"   Nasdaq 100 成員：{sum(1 for c in companies if c.get('nasdaq100'))} 間")
        total_updated += updated

    if not args.qqq_only:
        print("\n🔄 同步 SPY 持倉權重...")
        spy_weights = load_spy_holdings()
        updated = sync_spy(companies, spy_weights)
        print(f"   已更新 {updated} 間企業的 SPY 資料")
        print(f"   S&P 500 成員：{sum(1 for c in companies if c.get('in_sp500'))} 間")
        total_updated += updated

    save_companies(companies)
    print(f"\n✅ 同步完成！共更新 {total_updated} 筆資料")
    print(f"\n📌 後續步驟：")
    print(f"   1. python3 scripts/generate_update_log.py")
    print(f"   2. python3 scripts/generate_pages.py")


if __name__ == '__main__':
    main()
