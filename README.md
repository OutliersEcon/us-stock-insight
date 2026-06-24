# 🗺️ US Stock Insight (美股業務透視)

**US Stock Insight** 是一個由 AI Agent 驅動的開源專案，旨在為投資者提供標普 500 (SPY ETF) 成分股的深度業務解析。本專案會自動追蹤 SPY 的持倉變化，並利用 AI 技術分析每間公司的核心業務及其各個業務板塊對總收入的貢獻比例，最終透過 GitHub Pages 提供直觀、免費的靜態網頁供大眾查閱。

🌐 **網站入口**：[US Stock Insight GitHub Pages](https://outliersecon.github.io/us-stock-insight/) *(請確認 GitHub Pages 已在倉庫設定中啟用並指向 `main` 分支)*

---

## ✨ 核心功能 (Features)

- **🔄 自動化持倉同步**：定期下載並解析 SPY ETF 的最新持倉清單，確保名單涵蓋美國最重要的核心企業。
- **🤖 AI 業務解析**：利用 AI Agent 自動檢索並總結每間公司的核心業務模式。
- **📊 營收結構拆解**：精確列出各個業務部門（Segments）對公司總收入的貢獻比例，並以圓餅圖視覺化呈現。
- **📅 更新狀態追蹤**：所有企業頁面與主頁均顯示資料的**最後更新日期**，確保投資人參考的是最新資訊。
- **🏷️ 指數與行業標籤**：自動比對 QQQ ETF 持倉，為符合條件的企業標示 **Nasdaq 100** Badge，並提供中英雙語的行業分類篩選。
- **🌐 零成本託管**：完全基於 GitHub Pages 部署，採用純 HTML/CSS/JS 靜態網站架構，實現極速載入與零伺服器成本。

---

## 🏗️ 系統架構與 Workflow (Architecture & Workflow)

本專案採用現代化的 Serverless 與靜態網站架構，透過 GitHub 提供的生態系完成所有工作：

### 1. 數據獲取與處理層 (Data Fetching & Processing)
- **SPY 持倉獲取器** (`scripts/fetch_spy_holdings.py`)：自動從 State Street 抓取最新的 SPY 成分股 CSV 檔案。
- **AI Agent 處理器** (`scripts/ai_agent_parser.py`)：讀取持倉清單，呼叫 OpenAI API 解析各公司的最新財報（SEC EDGAR），結構化提取營收佔比，輸出統一格式的 JSON 檔案至 `data/processed/companies.json`。
- **內部更新追蹤日誌** (`scripts/generate_update_log.py`)：每次更新後，自動從 `companies.json` 生成 `data/update_log.json`。

### 2. 內部文件設計：`update_log.json`
為避免 AI 產生幻覺並節省 API Token，專案設計了自動生成的內部追蹤文件 `update_log.json`。
- **完全自動生成**：此檔案由 Python 腳本根據 `companies.json` 內的 `last_updated` 欄位自動計算與生成，**不依賴 AI 判斷或人工輸入**，確保資料 100% 準確。
- **AI 任務指引**：AI Agent 執行更新時會優先讀取此檔案，跳過近期（例如 30 天內）已更新的企業，集中資源更新超過閾值的過期資料。

### 3. 前端展示與靜態頁面生成 (Frontend Generation)
- **頁面生成器** (`scripts/generate_pages.py`)：讀取 `companies.json`，透過 Python 腳本動態生成：
  1. `index.html`：包含搜尋、中英雙語行業過濾、Nasdaq 100 篩選與所有公司卡片的總覽主頁。
  2. `stocks/*.html`：每間公司的獨立詳細頁面，包含 Chart.js 圓餅圖與最後更新日期。
- **多 Ticker 命名規則**：
  - **一般 Ticker**：直接使用大寫字母，例如 `AAPL` → `AAPL.html`。
  - **含特殊字元 (`.`, `/`) 的 Ticker**：將特殊字元替換為 `-`，例如 `BRK.B` 轉換為 `BRK-B.html`。

### 4. 自動化工作流 (GitHub Actions Automation)
專案規劃了 `.github/workflows/data-update.yml`（需授予 `workflows` 權限後推送），實現完全無人值守的自動化更新流程：
1. **觸發條件**：每週一 UTC 02:00 定時執行（Cron Job），或手動觸發 (workflow_dispatch)。
2. **執行步驟**：
   - 檢出程式碼並設定 Python 環境。
   - 執行 `fetch_spy_holdings.py` 更新原始持倉數據。
   - 執行 `ai_agent_parser.py` 呼叫 AI 更新過期的公司營收結構 JSON。
   - 執行 `generate_update_log.py` 重新計算更新日誌。
   - 執行 `generate_pages.py` 重新生成所有 HTML 頁面。
   - 將更新後的檔案 `git commit` 並 `push` 回 `main` 分支。
3. **自動部署**：GitHub Pages 偵測到 `main` 分支有更新後，會自動部署最新的靜態網頁。

---

## 📂 目錄結構 (Directory Structure)

```text
us-stock-insight/
├── .github/workflows/
│   └── data-update.yml        # GitHub Actions 自動化更新腳本
├── data/
│   ├── raw/                   # 存放原始抓取的 SPY Excel/CSV 資料
│   ├── processed/             # 存放 AI 處理後的 companies.json
│   └── update_log.json        # 自動生成的更新追蹤日誌
├── scripts/
│   ├── fetch_spy_holdings.py  # 抓取 SPY 持倉的 Python 腳本
│   ├── ai_agent_parser.py     # 呼叫 LLM 提取營收佔比的腳本骨架
│   ├── generate_update_log.py # 生成更新追蹤日誌的腳本
│   └── generate_pages.py      # 根據 JSON 批量生成 HTML 頁面的腳本
├── stocks/                    # 動態生成的個別企業 HTML 頁面 (例如 AAPL.html)
├── index.html                 # 網站主頁 (包含搜尋與過濾功能)
├── requirements.txt           # Python 依賴清單
└── README.md                  # 專案說明文件 (本文)
```

---

## 🗺️ 開發路線圖 (Roadmap)

- [x] 建立基礎 GitHub 儲存庫與 README
- [x] 實作 SPY 持倉自動下載腳本 (`fetch_spy_holdings.py`)
- [x] 設計 AI Agent 腳本骨架與 JSON 資料結構 (`ai_agent_parser.py`)
- [x] 建立前端 UI (包含搜尋、過濾、圓餅圖視覺化) (`index.html`)
- [x] 實作批量生成企業獨立頁面的自動化腳本 (`generate_pages.py`)
- [x] 制定多 Ticker 企業的檔案命名規則 (例如 `BRK.B` -> `BRK-B.html`)
- [x] 整合 Nasdaq 100 指數成分股標示與行業中文譯名
- [x] 實作自動化的內部更新追蹤日誌 (`update_log.json`)
- [ ] 完善 `ai_agent_parser.py` 整合 OpenAI API 與 SEC 數據的實際呼叫邏輯
- [ ] 授予 GitHub Actions `workflows` 權限，推送並啟用自動化 CI/CD 腳本
