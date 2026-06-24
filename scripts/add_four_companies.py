#!/usr/bin/env python3
"""
為 IBKR、ONDS、RCAT、IONQ 生成企業資料並加入 companies.json
這四間企業均不在 S&P 500 或 Nasdaq 100 指數內（自選企業）
"""

import json
import os
from openai import OpenAI

client = OpenAI()

COMPANIES_PATH = "data/processed/companies.json"
TODAY = "2026-06-24"

NEW_COMPANIES = [
    {
        "ticker": "IBKR",
        "name": "Interactive Brokers Group Inc.",
        "sector": "Financials",
    },
    {
        "ticker": "ONDS",
        "name": "Ondas Holdings Inc.",
        "sector": "Technology",
    },
    {
        "ticker": "RCAT",
        "name": "Red Cat Holdings Inc.",
        "sector": "Industrials",
    },
    {
        "ticker": "IONQ",
        "name": "IonQ Inc.",
        "sector": "Technology",
    },
]

PROMPT_TEMPLATE = """You are a financial analyst. Provide structured data for the following US-listed company.

Company: {name} (Ticker: {ticker})
Sector: {sector}

Return ONLY a valid JSON object with these exact fields:
{{
  "description": "<繁體中文，2-3句，描述公司核心業務模式>",
  "revenue_segments": [
    {{"segment": "<英文業務板塊名稱>", "percentage": <整數佔比>, "description": "<繁體中文說明>"}},
    ...
  ]
}}

Rules:
- description must be in Traditional Chinese (繁體中文)
- revenue_segments descriptions must be in Traditional Chinese (繁體中文)
- segment names should be in English
- percentages must sum to 100
- sort revenue_segments by percentage descending
- provide 2-5 segments based on actual business structure
- use the most recent fiscal year data available
- return ONLY the JSON object, no markdown, no explanation
"""

def generate_company_data(ticker, name, sector):
    prompt = PROMPT_TEMPLATE.format(ticker=ticker, name=name, sector=sector)
    print(f"  Generating data for {ticker}...")
    
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="claude-sonnet-4-6",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3,
            )
            content = response.choices[0].message.content
            if not content:
                print(f"  [{ticker}] Empty response, attempt {attempt+1}")
                continue
            
            # Strip markdown code blocks if present
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            data = json.loads(content)
            print(f"  [{ticker}] OK - {len(data['revenue_segments'])} segments")
            return data
        except json.JSONDecodeError as e:
            print(f"  [{ticker}] JSON parse error attempt {attempt+1}: {e}")
            print(f"  Raw: {content[:200]}")
        except Exception as e:
            print(f"  [{ticker}] Error attempt {attempt+1}: {e}")
    
    return None

def main():
    # Load existing companies.json
    with open(COMPANIES_PATH, "r", encoding="utf-8") as f:
        companies = json.load(f)
    
    existing_tickers = {c["ticker"] for c in companies}
    print(f"Current companies: {len(companies)}")
    
    added = 0
    for company in NEW_COMPANIES:
        ticker = company["ticker"]
        
        if ticker in existing_tickers:
            print(f"[SKIP] {ticker} already exists")
            continue
        
        print(f"\nProcessing {ticker} - {company['name']}...")
        ai_data = generate_company_data(ticker, company["name"], company["sector"])
        
        if not ai_data:
            print(f"[FAIL] Could not generate data for {ticker}")
            continue
        
        # Sort segments by percentage descending
        segments = sorted(ai_data["revenue_segments"], key=lambda x: x["percentage"], reverse=True)
        
        entry = {
            "ticker": ticker,
            "name": company["name"],
            "sector": company["sector"],
            "description": ai_data["description"],
            "weight": 0.0,          # Not in SPY
            "last_updated": TODAY,
            "nasdaq100": False,
            "revenue_segments": segments,
            "in_sp500": False,
            "qqq_weight": 0.0,      # Not in QQQ
        }
        
        companies.append(entry)
        existing_tickers.add(ticker)
        added += 1
        print(f"[OK] Added {ticker}")
    
    # Save updated companies.json
    with open(COMPANIES_PATH, "w", encoding="utf-8") as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)
    
    print(f"\nDone! Added {added} companies. Total: {len(companies)}")

if __name__ == "__main__":
    main()
