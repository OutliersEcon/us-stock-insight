"""
bulk_add_companies.py
=====================
批量新增 S&P 500 成分股至 companies.json。
使用 OpenAI API 為每間新企業生成業務描述與營收結構。
"""

import json
import os
import time
from datetime import date
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMPANIES_FILE = os.path.join(BASE_DIR, '..', 'data', 'processed', 'companies.json')
TODAY = date.today().isoformat()

client = OpenAI()  # 使用環境變數 OPENAI_API_KEY 與 OPENAI_API_BASE

# ── Nasdaq 100 成員（從 QQQ 持倉確認）
NASDAQ100 = {
    "NVDA","AAPL","MSFT","AMZN","GOOGL","GOOG","AVGO","TSLA","META","WMT",
    "AMD","COST","NFLX","INTC","CSCO","TXN","QCOM","AMGN","INTU","ISRG",
    "ADI","AMAT","LRCX","PANW","SNPS","CDNS","MRVL","KLAC","CRWD","FTNT",
    "TMUS","REGN","VRTX","GILD","MDLZ","MNST","ABNB","DDOG","MELI","PYPL",
    "SBUX","ADBE","MU","NXPI","ASML","AZN","LULU","BKNG","HOOD","APP",
    "KDP","CTAS","FAST","PCAR","ODFL","VRSK","CTSH","BIIB","IDXX","ILMN",
    "TEAM","ZS","OKTA","SIRI","WDAY","DLTR","EBAY","SGEN","TTWO","NTES",
    "PDD","MCHP","ROST","ORLY","CPRT","PAYX","CHTR","CMCSA","ATVI","EA",
    "WBA","MRNA","ALGN","DXCM","LCID","RIVN","ENPH","CEG"
}

# ── 行業分類對照
SECTOR_MAP = {
    "NVDA":"Technology","AAPL":"Technology","MSFT":"Technology","AMZN":"Consumer Discretionary",
    "GOOGL":"Communication Services","GOOG":"Communication Services","AVGO":"Technology",
    "TSLA":"Consumer Discretionary","META":"Communication Services","MU":"Technology",
    "BRK.B":"Financials","LLY":"Healthcare","WMT":"Consumer Staples","JPM":"Financials",
    "AMD":"Technology","INTC":"Technology","V":"Financials","XOM":"Energy","JNJ":"Healthcare",
    "ORCL":"Technology","LRCX":"Technology","AMAT":"Technology","CSCO":"Technology",
    "CAT":"Industrials","MA":"Financials","COST":"Consumer Staples","ABBV":"Healthcare",
    "BAC":"Financials","UNH":"Healthcare","GE":"Industrials","MS":"Financials",
    "CVX":"Energy","KO":"Consumer Staples","PG":"Consumer Staples","KLAC":"Technology",
    "HD":"Consumer Discretionary","GS":"Financials","NFLX":"Communication Services",
    "SNDK":"Technology","GEV":"Industrials","TXN":"Technology","MRK":"Healthcare",
    "PLTR":"Technology","PM":"Consumer Staples","DELL":"Technology","WFC":"Financials",
    "IBM":"Technology","MRVL":"Technology","C":"Financials","RTX":"Industrials",
    "LIN":"Materials","WDC":"Technology","PANW":"Technology","STX":"Technology",
    "AXP":"Financials","QCOM":"Technology","ANET":"Technology","ADI":"Technology",
    "APH":"Technology","TMUS":"Communication Services","PEP":"Consumer Staples",
    "MCD":"Consumer Discretionary","VZ":"Communication Services","AMGN":"Healthcare",
    "TJX":"Consumer Discretionary","NEE":"Utilities","DIS":"Communication Services",
    "BA":"Industrials","TMO":"Healthcare","CRWD":"Technology","GLW":"Technology",
    "ETN":"Industrials","BLK":"Financials","DE":"Industrials","SCHW":"Financials",
    "APP":"Technology","T":"Communication Services","UNP":"Industrials","GILD":"Healthcare",
    "ABT":"Healthcare","WELL":"Real Estate","BX":"Financials","UBER":"Technology",
    "HON":"Industrials","ISRG":"Healthcare","PFE":"Healthcare","COP":"Energy",
    "PLD":"Real Estate","VRT":"Technology","BKNG":"Consumer Discretionary","CVS":"Healthcare",
    "CB":"Financials","DHR":"Healthcare","COF":"Financials","CRM":"Technology",
    "PGR":"Financials","SPGI":"Financials","LOW":"Consumer Discretionary","PH":"Industrials",
    "VRTX":"Healthcare","MO":"Consumer Staples","SYK":"Healthcare","SBUX":"Consumer Discretionary",
    "LMT":"Industrials","BMY":"Healthcare","HWM":"Industrials","EQIX":"Real Estate",
    "PWR":"Industrials","TT":"Industrials","CDNS":"Technology","FTNT":"Technology",
    "SO":"Utilities","NEM":"Materials","MDT":"Healthcare","MAR":"Consumer Discretionary",
    "BNY":"Financials","CMI":"Industrials","NOW":"Technology","DUK":"Utilities",
    "CEG":"Utilities","FCX":"Materials","PNC":"Financials","GD":"Industrials",
    "MNST":"Consumer Staples","HOOD":"Financials","WMB":"Energy","USB":"Financials",
    "UPS":"Industrials","CME":"Financials","SNPS":"Technology","JCI":"Industrials",
    "MCK":"Healthcare","KKR":"Financials","WM":"Industrials","ADP":"Technology",
    "CSX":"Industrials","MMM":"Industrials","ELV":"Healthcare","HCA":"Healthcare",
    "EMR":"Industrials","ABNB":"Consumer Discretionary","AMT":"Real Estate",
    "RCL":"Consumer Discretionary","CMCSA":"Communication Services","NXPI":"Technology",
    "SHW":"Materials","DDOG":"Technology","ADBE":"Technology","FDX":"Industrials",
    "MCO":"Financials","MDLZ":"Consumer Staples","COHR":"Technology","HLT":"Consumer Discretionary",
    "ACN":"Technology","MRSH":"Financials","APO":"Financials","ECL":"Materials",
    "ITW":"Industrials","CI":"Healthcare","DASH":"Technology","ROST":"Consumer Discretionary",
    "ICE":"Financials","CRH":"Materials","NOC":"Industrials","MPC":"Energy",
    "VLO":"Energy","TDG":"Industrials","GM":"Consumer Discretionary","CL":"Consumer Staples",
    "MPWR":"Technology","KMI":"Energy","SLB":"Energy","ORLY":"Consumer Discretionary",
    "INTU":"Technology","AEP":"Utilities","EOG":"Energy",
}

# ── 新增企業清單（S&P 500 前 150 中尚未收錄的）
NEW_COMPANIES = [
    ("MU",    "Micron Technology Inc.",           0.89),
    ("INTC",  "Intel Corporation",                0.98),
    ("LRCX",  "Lam Research Corporation",         0.71),
    ("AMAT",  "Applied Materials Inc.",           0.70),
    ("CSCO",  "Cisco Systems Inc.",               0.70),
    ("CAT",   "Caterpillar Inc.",                 0.69),
    ("ABBV",  "AbbVie Inc.",                      0.61),
    ("GE",    "General Electric Company",         0.55),
    ("MS",    "Morgan Stanley",                   0.53),
    ("KLAC",  "KLA Corporation",                  0.49),
    ("SNDK",  "Sandisk Corporation",              0.46),
    ("GEV",   "GE Vernova Inc.",                  0.43),
    ("TXN",   "Texas Instruments Incorporated",   0.43),
    ("PLTR",  "Palantir Technologies Inc.",        0.43),
    ("PM",    "Philip Morris International Inc.", 0.41),
    ("DELL",  "Dell Technologies Inc.",           0.38),
    ("WFC",   "Wells Fargo & Company",            0.38),
    ("IBM",   "International Business Machines Corporation", 0.37),
    ("MRVL",  "Marvell Technology Inc.",          0.37),
    ("C",     "Citigroup Inc.",                   0.37),
    ("RTX",   "RTX Corporation",                  0.36),
    ("LIN",   "Linde PLC",                        0.36),
    ("WDC",   "Western Digital Corporation",      0.35),
    ("PANW",  "Palo Alto Networks Inc.",          0.34),
    ("AXP",   "American Express Company",         0.34),
    ("QCOM",  "QUALCOMM Incorporated",            0.33),
    ("ANET",  "Arista Networks Inc.",             0.31),
    ("ADI",   "Analog Devices Inc.",              0.31),
    ("APH",   "Amphenol Corporation",             0.29),
    ("TMUS",  "T-Mobile US Inc.",                 0.29),
    ("PEP",   "PepsiCo Inc.",                     0.29),
    ("MCD",   "McDonald's Corporation",           0.29),
    ("VZ",    "Verizon Communications Inc.",      0.28),
    ("AMGN",  "Amgen Inc.",                       0.28),
    ("TJX",   "The TJX Companies Inc.",           0.27),
    ("NEE",   "NextEra Energy Inc.",              0.27),
    ("BA",    "The Boeing Company",               0.26),
    ("TMO",   "Thermo Fisher Scientific Inc.",    0.26),
    ("CRWD",  "CrowdStrike Holdings Inc.",        0.25),
    ("GLW",   "Corning Inc.",                     0.25),
    ("ETN",   "Eaton Corporation PLC",            0.24),
    ("BLK",   "BlackRock Inc.",                   0.24),
    ("DE",    "Deere & Company",                  0.24),
    ("SCHW",  "The Charles Schwab Corporation",   0.24),
    ("APP",   "AppLovin Corporation",             0.23),
    ("T",     "AT&T Inc.",                        0.23),
    ("UNP",   "Union Pacific Corporation",        0.23),
    ("GILD",  "Gilead Sciences Inc.",             0.23),
    ("ABT",   "Abbott Laboratories",              0.23),
    ("WELL",  "Welltower Inc.",                   0.22),
    ("BX",    "Blackstone Inc.",                  0.22),
    ("UBER",  "Uber Technologies Inc.",           0.22),
    ("HON",   "Honeywell International Inc.",     0.21),
    ("ISRG",  "Intuitive Surgical Inc.",          0.21),
    ("PFE",   "Pfizer Inc.",                      0.21),
    ("COP",   "ConocoPhillips",                   0.20),
    ("PLD",   "Prologis Inc.",                    0.20),
    ("VRT",   "Vertiv Holdings Co.",              0.19),
    ("BKNG",  "Booking Holdings Inc.",            0.19),
    ("CVS",   "CVS Health Corporation",           0.19),
    ("CB",    "Chubb Limited",                    0.19),
    ("DHR",   "Danaher Corporation",              0.19),
    ("COF",   "Capital One Financial Corporation",0.19),
    ("CRM",   "Salesforce Inc.",                  0.18),
    ("PGR",   "The Progressive Corporation",      0.18),
    ("SPGI",  "S&P Global Inc.",                  0.18),
    ("LOW",   "Lowe's Companies Inc.",            0.18),
    ("VRTX",  "Vertex Pharmaceuticals Incorporated", 0.18),
    ("MO",    "Altria Group Inc.",                0.18),
    ("SYK",   "Stryker Corporation",              0.17),
    ("SBUX",  "Starbucks Corporation",            0.17),
    ("LMT",   "Lockheed Martin Corporation",      0.17),
    ("BMY",   "Bristol-Myers Squibb Company",     0.17),
    ("NOW",   "ServiceNow Inc.",                  0.14),
    ("ADBE",  "Adobe Inc.",                       0.12),
    ("CMCSA", "Comcast Corporation",              0.12),
    ("NXPI",  "NXP Semiconductors N.V.",          0.12),
    ("ACN",   "Accenture PLC",                    0.12),
    ("INTU",  "Intuit Inc.",                      0.11),
    ("ADP",   "Automatic Data Processing Inc.",   0.13),
    ("SNPS",  "Synopsys Inc.",                    0.13),
    ("CDNS",  "Cadence Design Systems Inc.",      0.16),
    ("FTNT",  "Fortinet Inc.",                    0.16),
    ("AMZN",  "Amazon.com Inc.",                  3.71),  # already in, skip
]

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


def call_ai(ticker, name, sector):
    prompt = USER_PROMPT_TEMPLATE.format(name=name, ticker=ticker, sector=sector)
    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=2000
        )
        result = json.loads(response.choices[0].message.content)
        if 'description' not in result or 'revenue_segments' not in result:
            return None
        total = sum(s.get('percentage', 0) for s in result['revenue_segments'])
        if total != 100:
            result['revenue_segments'][-1]['percentage'] += (100 - total)
        return result
    except Exception as e:
        print(f"   ❌ API 錯誤：{e}")
        return None


def main():
    # 讀取現有資料
    with open(COMPANIES_FILE, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    existing_tickers = {c['ticker'] for c in companies}
    print(f"現有企業數：{len(existing_tickers)}")

    # 過濾出真正需要新增的企業
    to_add = [
        (ticker, name, weight)
        for ticker, name, weight in NEW_COMPANIES
        if ticker.replace('.', '-') not in existing_tickers and ticker not in existing_tickers
    ]
    print(f"待新增企業數：{len(to_add)}")
    print()

    added = 0
    for i, (ticker, name, weight) in enumerate(to_add):
        file_ticker = ticker.replace('.', '-')
        sector = SECTOR_MAP.get(ticker, "Technology")
        nasdaq100 = ticker in NASDAQ100

        print(f"[{i+1:02d}/{len(to_add)}] 新增 {ticker} ({name})...")
        result = call_ai(ticker, name, sector)
        if result:
            companies.append({
                "ticker": file_ticker,
                "name": name,
                "sector": sector,
                "description": result['description'],
                "weight": weight,
                "last_updated": TODAY,
                "nasdaq100": nasdaq100,
                "revenue_segments": result['revenue_segments']
            })
            added += 1
            print(f"   ✓ 成功（{len(result['revenue_segments'])} 個板塊）")
        else:
            print(f"   ⚠️  失敗，跳過。")

        if i < len(to_add) - 1:
            time.sleep(0.5)

    # 按 weight 降冪排序
    companies.sort(key=lambda c: c['weight'], reverse=True)

    # 寫回
    with open(COMPANIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)

    print()
    print(f"✅ 完成！新增 {added} 間企業，總計 {len(companies)} 間。")


if __name__ == '__main__':
    main()
