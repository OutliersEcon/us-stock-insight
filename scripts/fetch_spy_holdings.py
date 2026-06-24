import pandas as pd
import requests
from io import StringIO
import os

def fetch_spy_holdings():
    """
    抓取 SPY ETF 最新持倉清單並儲存為 CSV。
    數據來源：State Street Global Advisors (SSGA)
    """
    # SPY 持倉 CSV 下載連結 (SSGA 官方)
    url = "https://www.ssga.com/us/en/intermediary/etfs/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx"

    print("正在下載 SPY 持倉數據...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        os.makedirs("data/raw", exist_ok=True)
        output_path = "data/raw/spy_holdings_raw.xlsx"

        with open(output_path, "wb") as f:
            f.write(response.content)

        print(f"成功儲存原始持倉數據至 {output_path}")

    except Exception as e:
        print(f"下載失敗: {e}")

if __name__ == "__main__":
    fetch_spy_holdings()
