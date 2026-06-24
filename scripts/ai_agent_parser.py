import json
import os

def parse_company_revenue(ticker: str, company_name: str) -> dict:
    """
    使用 AI Agent 解析公司的營收結構。
    整合 OpenAI API 與財報數據源 (SEC EDGAR)。
    """
    # TODO: 整合 OpenAI API 呼叫
    # TODO: 整合 SEC EDGAR 財報數據源
    
    result = {
        "ticker": ticker,
        "name": company_name,
        "description": "",
        "last_updated": "",
        "revenue_segments": []
    }
    return result

def save_company_data(data: dict):
    """將結構化數據儲存為 JSON 檔案。"""
    os.makedirs("data/processed", exist_ok=True)
    output_path = f"data/processed/{data['ticker'].lower()}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已儲存 {data['ticker']} 數據至 {output_path}")

if __name__ == "__main__":
    # 範例：解析 Apple 的營收結構
    data = parse_company_revenue("AAPL", "Apple Inc.")
    save_company_data(data)
