"""
add_qqq_weights.py
==================
將 QQQ 持倉權重加入 companies.json 的 qqq_weight 欄位。
非 Nasdaq 100 成員的企業 qqq_weight 設為 0。
"""

import json
import os

COMPANIES_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'companies.json')

# QQQ 持倉權重資料（來源：slickcharts.com/nasdaq100，2026-06-24）
QQQ_WEIGHTS = {
    "NVDA": 12.90,
    "AAPL": 11.08,
    "MSFT": 7.04,
    "AMZN": 6.44,
    "GOOGL": 5.58,
    "GOOG": 5.22,
    "AVGO": 4.80,
    "TSLA": 3.79,
    "META": 3.65,
    "MU": 3.33,
    "WMT": 2.35,
    "AMD": 2.28,
    "ASML": 1.86,
    "INTC": 1.74,
    "AMAT": 1.25,
    "LRCX": 1.24,
    "CSCO": 1.19,
    "ARM": 1.14,
    "COST": 1.05,
    "KLAC": 0.86,
    "SNDK": 0.84,
    "NFLX": 0.81,
    "PLTR": 0.77,
    "TXN": 0.75,
    "MRVL": 0.67,
    "WDC": 0.65,
    "STX": 0.63,
    "PANW": 0.60,
    "QCOM": 0.60,
    "LIN": 0.59,
    "ADI": 0.54,
    "TMUS": 0.49,
    "PEP": 0.49,
    "AMGN": 0.46,
    "CRWD": 0.45,
    "APP": 0.40,
    "GILD": 0.39,
    "HON": 0.37,
    "ISRG": 0.36,
    "SHOP": 0.36,
    "BKNG": 0.33,
    "VRTX": 0.29,
    "SBUX": 0.29,
    "PDD": 0.28,
    "FTNT": 0.27,
    "CDNS": 0.27,
    "MAR": 0.26,
    "CEG": 0.25,
    "MNST": 0.23,
    "SNPS": 0.22,
    "ADP": 0.22,
    "CSX": 0.21,
    "ABNB": 0.21,
    "MELI": 0.21,
    "NXPI": 0.20,
    "CMCSA": 0.20,
    "DDOG": 0.20,
    "ADBE": 0.20,
    "MDLZ": 0.19,
    "ROST": 0.19,
    "MPWR": 0.19,
    "DASH": 0.19,
    "ALAB": 0.19,
    "NBIS": 0.19,
    "INTU": 0.18,
    "ORLY": 0.18,
    "AEP": 0.18,
    "TER": 0.17,
    "CTAS": 0.17,
    "WBD": 0.17,
    "LITE": 0.17,
    "REGN": 0.16,
    "RKLB": 0.16,
    "CRWV": 0.16,
    "PCAR": 0.16,
    "BKR": 0.14,
    "MCHP": 0.14,
    "FAST": 0.13,
    "FANG": 0.13,
    "EA": 0.13,
    "FER": 0.12,
    "XEL": 0.12,
    "EXC": 0.12,
    "TTWO": 0.12,
    "ODFL": 0.12,
    "IDXX": 0.11,
    "CCEP": 0.11,
    "MSTR": 0.11,
    "KDP": 0.10,
    "ADSK": 0.10,
    "PYPL": 0.10,
    "ALNY": 0.09,
    "PAYX": 0.09,
    "TRI": 0.09,
    "ROP": 0.08,
    "AXON": 0.08,
    "WDAY": 0.07,
    "GEHC": 0.07,
    "CPRT": 0.07,
    "DXCM": 0.07,
    "KHC": 0.07,
}

def main():
    with open(COMPANIES_FILE, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    updated = 0
    for c in companies:
        ticker = c['ticker']
        qqq_w = QQQ_WEIGHTS.get(ticker, 0)
        c['qqq_weight'] = qqq_w
        if qqq_w > 0:
            updated += 1
            # 確保 nasdaq100 欄位與 QQQ 資料一致
            c['nasdaq100'] = True

    with open(COMPANIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)

    print(f"✅ 已更新 {len(companies)} 間企業的 qqq_weight 欄位")
    print(f"   其中 {updated} 間企業有 QQQ 權重資料")
    print(f"   其餘 {len(companies) - updated} 間企業 qqq_weight = 0")

if __name__ == '__main__':
    main()
