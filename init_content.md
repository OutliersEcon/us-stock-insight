# US Stock Insight (美股業務透視) 初始內容規劃

根據 `README.md` 的描述，這個專案的核心目標是提供標普 500 (SPY ETF) 成分股的深度業務解析，並透過自動化腳本與 AI 分析，最終在 GitHub Pages 上呈現靜態網頁。

為了實現開發路線圖中的第一階段與後續階段，以下是專案的初始內容結構規劃與部分基礎程式碼草稿：

## 1. 專案目錄結構規劃

建議在 `us-stock-insight` 倉庫中建立以下目錄結構：

```text
us-stock-insight/
├── .github/
│   └── workflows/
│       └── data-update.yml    # GitHub Actions 自動化更新腳本
├── data/
│   ├── raw/                   # 存放原始抓取的 SPY CSV 資料
│   └── processed/             # 存放 AI 處理後的 JSON 資料
├── scripts/
│   ├── fetch_spy_holdings.py  # 抓取 SPY 持倉的 Python 腳本
│   └── ai_agent_parser.py     # 呼叫 LLM 提取營收佔比的腳本
├── frontend/                  # 前端靜態網站程式碼 (Next.js/Astro)
│   ├── src/
│   ├── public/
│   └── package.json
├── README.md
└── requirements.txt           # Python 依賴清單
```

## 2. 初始腳本草稿：抓取 SPY 持倉

根據路線圖「實作 SPY 持倉自動下載腳本」，可以建立一個基礎的 Python 腳本 `scripts/fetch_spy_holdings.py` 來抓取 ETF 數據。

```python
import pandas as pd
import requests
from io import StringIO
import os

def fetch_spy_holdings():
    # 這裡替換為實際的 SPY 持倉 CSV 下載連結 (例如 State Street 官網)
    url = "https://example.com/spy_holdings.csv" 
    
    print("正在下載 SPY 持倉數據...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # 假設 CSV 包含 Ticker, Name, Weight 等欄位
        df = pd.read_csv(StringIO(response.text))
        
        # 確保資料夾存在
        os.makedirs("../data/raw", exist_ok=True)
        
        # 儲存原始資料
        output_path = "../data/raw/spy_holdings.csv"
        df.to_csv(output_path, index=False)
        print(f"成功儲存持倉數據至 {output_path}")
        
    except Exception as e:
        print(f"下載失敗: {e}")

if __name__ == "__main__":
    fetch_spy_holdings()
```

## 3. 初始 JSON 資料結構設計

AI Agent 處理後的資料應統一格式，以利前端渲染。建議的 `data/processed/company_data.json` 結構如下：

```json
{
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "description": "Apple 是一家跨國科技公司，專注於消費電子、軟體與線上服務。",
  "last_updated": "2023-10-25",
  "revenue_segments": [
    {
      "segment": "iPhone",
      "percentage": 52.1,
      "description": "智慧型手機銷售"
    },
    {
      "segment": "Services",
      "percentage": 22.0,
      "description": "App Store, Apple Music, iCloud 等服務"
    },
    {
      "segment": "Mac",
      "percentage": 7.7,
      "description": "個人電腦銷售"
    }
  ]
}
```

## 4. 下一步行動建議

1. **確認前端框架**：決定使用 Next.js、Astro 或其他靜態網站生成器，並初始化 `frontend` 目錄。
2. **尋找穩定的 SPY 數據源**：確認 State Street 或其他來源的 CSV 下載連結。
3. **設計 AI Prompt**：為 `ai_agent_parser.py` 設計能精準從財報中提取營收佔比的提示詞 (Prompt)。
