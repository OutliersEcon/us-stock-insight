# 🗺️ US Stock Insight (美股業務透視)

**US Stock Insight** 是一個由 AI Agent 驅動的開源專案，旨在為投資者提供美股核心企業的深度業務解析。本專案不僅自動追蹤標普 500 (SPY ETF) 的持倉變化，亦支援收錄不在 S&P 500 指數內的精選企業。透過 AI 技術分析每間公司的核心業務及其各個業務板塊對總收入的貢獻比例，最終透過 GitHub Pages 提供直觀、免費的靜態網頁供大眾查閱。

🌐 **網站入口**：[US Stock Insight GitHub Pages](https://outliersecon.github.io/us-stock-insight/) *(請確認 GitHub Pages 已在倉庫設定中啟用並指向 `main` 分支)*

---

## ✨ 核心功能 (Features)

- **🔄 自動化持倉同步**：定期下載並解析 SPY ETF 的最新持倉清單，目前已收錄 **116 間** 核心企業（包含 S&P 500 成分股及精選自選企業）。
- **🤖 AI 業務解析**：利用 AI Agent 自動檢索並總結每間公司的核心業務模式。
- **📊 營收結構拆解**：精確列出各個業務部門（Segments）對公司總收入的貢獻比例，並以圓餅圖視覺化呈現。
- **📅 更新狀態追蹤**：所有企業頁面與主頁均顯示資料的**最後更新日期**，確保投資人參考的是最新資訊。
- **🏷️ 智慧篩選與排序**：
  - **指數篩選**：可一鍵切換「全部」、「只看 S&P 500」、「只看 Nasdaq 100」。非 S&P 500 企業會有專屬的「自選」標籤。
  - **行業篩選**：提供中英雙語的行業分類按鈕（如：Technology 科技、Financials 金融）。
  - **排序功能**：支援按 SPY 權重、QQQ 權重、代號 (A-Z) 或名稱 (A-Z) 排序（非 S&P 500 企業固定排在列表最後）。
  - **分頁功能 (Pagination)**：支援每頁顯示 25 / 50 / 100 間或全部企業，頁碼導覽列同時顯示於列表**上方和下方**，方便大量瀏覽。
  - **清除篩選**：提供一鍵 Reset 按鈕，快速恢復預設視圖（含重置分頁至第一頁）。
  - **智慧搜尋**：支援按 Ticker、公司名稱、行業，甚至是**常見別名**搜尋（例如搜尋「Google」可找到 GOOGL，搜尋「巴菲特」可找到 BRK-B）。
- **🌐 零成本託管**：完全基於 GitHub Pages 部署，採用純 HTML/CSS/JS 靜態網站架構，實現極速載入與零伺服器成本。

---

## 🏗️ 系統架構與 Workflow (Architecture & Workflow)

本專案採用現代化的 Serverless 與靜態網站架構，透過 GitHub 提供的生態系完成所有工作：

### 1. 數據獲取與處理層 (Data Fetching & Processing)

`scripts/` 資料夾採用**職責單一、可重複使用**的設計原則，每個腳本均有明確用途：

| 腳本 | 用途 |
|---|---|
| `fetch_spy_holdings.py` | 自動從 State Street 抓取最新的 SPY 成分股 CSV 檔案 |
| `add_companies.py` | **通用企業新增工具**：透過 AI 為任意 Ticker 清單生成業務描述與營收結構，支援命令列參數（見下方說明）|
| `sync_index_data.py` | **指數資料同步工具**：統一管理 SPY/QQQ 持倉權重、`in_sp500` 與 `nasdaq100` 欄位的更新 |
| `ai_agent_parser.py` | **AI 定期更新器**：讀取 `update_log.json`，自動更新超過閾值（預設 30 天）的過期企業資料 |
| `generate_update_log.py` | 從 `companies.json` 自動生成 `data/update_log.json`，供 AI 更新器判斷哪些企業需要更新 |
| `generate_pages.py` | 根據 `companies.json` 批量生成所有 HTML 頁面（`index.html` 與 `stocks/*.html`）|

#### 新增企業的標準流程

```bash
# 1. 新增一間或多間企業（AI 自動生成業務描述與營收結構）
python3 scripts/add_companies.py TICKER1 TICKER2

# 新增 S&P 500 成員（加上 --sp500 旗標）
python3 scripts/add_companies.py --sp500 NEWSTOCK

# 強制覆蓋已存在的企業資料
python3 scripts/add_companies.py --overwrite AAPL

# 從文字檔批量新增（每行一個 Ticker，# 開頭為注釋）
python3 scripts/add_companies.py --file tickers.txt

# 2. 同步最新的 SPY/QQQ 持倉權重
python3 scripts/sync_index_data.py

# 3. 重新生成追蹤日誌與所有 HTML 頁面
python3 scripts/generate_update_log.py
python3 scripts/generate_pages.py
```

### 2. 內部文件設計：`update_log.json`
為避免 AI 產生幻覺並節省 API Token，專案設計了自動生成的內部追蹤文件 `update_log.json`。
- **完全自動生成**：此檔案由 Python 腳本根據 `companies.json` 自動計算與生成，包含 `last_updated` 追蹤、`in_sp500` 標記與 `nasdaq100` 標記，**不依賴 AI 判斷或人工輸入**，確保資料 100% 準確。
- **AI 任務指引**：AI Agent 執行更新時會優先讀取此檔案，跳過近期（例如 30 天內）已更新的企業，集中資源更新超過閾值的過期資料。

### 3. 前端展示與靜態頁面生成 (Frontend Generation)
- **頁面生成器** (`scripts/generate_pages.py`)：讀取 `companies.json`，透過 Python 腳本動態生成：
  1. `index.html`：總覽主頁，UI 樣式與 DOM 結構定義於此。
  2. `stocks/*.html`：每間公司的獨立詳細頁面，包含 Chart.js 圓餅圖與最後更新日期。
- **前端邏輯分離** (`app.js`)：
  - 主頁的所有互動邏輯（搜尋、排序、指數 toggle、行業篩選、動態渲染卡片）皆抽離至獨立的 `app.js` 檔案，保持 `index.html` 結構簡潔。
  - 內建 `SEARCH_ALIASES` 字典，解決常見縮寫或母公司名稱的搜尋體驗問題。
- **多 Ticker 命名規則**：
  - **一般 Ticker**：直接使用大寫字母，例如 `AAPL` → `AAPL.html`。
  - **含特殊字元 (`.`, `/`) 的 Ticker**：將特殊字元替換為 `-`，例如 `BRK.B` 轉換為 `BRK-B.html`。

### 4. 自動化工作流 (GitHub Actions Automation)
專案已部署 `.github/workflows/data-update.yml`，實現完全無人值守的自動化更新流程：
1. **觸發條件**：每週一 UTC 02:00 定時執行（Cron Job），或手動觸發 (workflow_dispatch)。
2. **執行步驟**：
   - 檢出程式碼並設定 Python 環境。
   - 執行 `fetch_spy_holdings.py` 更新原始持倉數據。
   - 執行 `ai_agent_parser.py` 呼叫 AI 更新過期的公司營收結構 JSON。
   - 執行 `generate_update_log.py` 重新計算更新日誌。
   - 執行 `generate_pages.py` 重新生成所有 HTML 頁面。
   - 將更新後的檔案 `git commit` 並 `push` 回 `main` 分支。
3. **自動部署**：GitHub Pages 偵測到 `main` 分支有更新後，會自動部署最新的靜態網頁。

> **💡 權限與 Token 設定說明**
> 為了讓 GitHub Actions 能成功執行，專案維護者已透過 Personal Access Token (PAT) 授予 `workflows` 權限，確保 `.github/workflows` 目錄下的 YAML 檔案能被正確推送並啟用定時排程。請注意，為了保護隱私，任何 Token 或 API 金鑰（如 `MANUS_API_KEY`）皆透過 GitHub 倉庫的 **Settings → Secrets and variables → Actions** 進行管理，絕不會明碼寫入程式碼或 README 中。

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
│   ├── add_companies.py       # 通用企業新增工具（支援任意 Ticker，可重複使用）
│   ├── sync_index_data.py     # SPY/QQQ 持倉權重與指數成員資料同步工具
│   ├── fetch_spy_holdings.py  # 抓取 SPY 持倉的 Python 腳本
│   ├── ai_agent_parser.py     # 呼叫 LLM 提取營收佔比的智慧更新腳本
│   ├── generate_update_log.py # 生成更新追蹤日誌的腳本
│   └── generate_pages.py      # 根據 JSON 批量生成 HTML 頁面的腳本
├── stocks/                    # 動態生成的個別企業 HTML 頁面 (例如 AAPL.html)
├── index.html                 # 網站主頁 UI 結構
├── app.js                     # 網站主頁前端互動邏輯 (搜尋/排序/篩選)
├── requirements.txt           # Python 依賴清單
└── README.md                  # 專案說明文件 (本文)
```

---

## 🗺️ 開發路線圖 (Roadmap)

- [x] 建立基礎 GitHub 儲存庫與 README
- [x] 實作 SPY 持倉自動下載腳本 (`fetch_spy_holdings.py`)
- [x] 建立前端 UI (包含搜尋、過濾、圓餅圖視覺化) (`index.html` & `app.js`)
- [x] 實作批量生成企業獨立頁面的自動化腳本 (`generate_pages.py`)
- [x] 制定多 Ticker 企業的檔案命名規則 (例如 `BRK.B` -> `BRK-B.html`)
- [x] 整合 Nasdaq 100 指數成分股標示與行業中文譯名
- [x] 實作自動化的內部更新追蹤日誌 (`update_log.json`)
- [x] 授予 GitHub Actions `workflows` 權限，推送並啟用自動化 CI/CD 腳本
- [x] 整合 MANUS_API_KEY，實作 `ai_agent_parser.py` 智能更新邏輯
- [x] 大幅擴充收錄企業範圍（從 30 間擴充至 S&P 500 前 150 大，共 113 間）
- [x] 前端重構：加入排序功能、指數 Toggle、優化搜尋體驗（支援別名搜尋）
- [x] 支援收錄非 S&P 500 之精選企業，並完善前端排序與標籤邏輯
- [x] 優化前端互動體驗：支援點擊已選中標籤取消篩選、確保 Reset 按鈕與計數器狀態正確
- [x] 修復搜尋過度匹配：別名改為單向比對（alias.includes(q)）、要求 q 至少 2 字元、公司名稱改用 word-boundary 匹配
- [x] 加入 `escapeHtml()` 將所有來自 JSON 的動態內容進行 HTML 變數轉義，防止 XSS 與版面崩潰風險
- [x] 修復業務板塊排序：`companies.json` 與個別頁面的 `revenue_segments` 均按百分比降床排序（大到小）
- [x] 加入 QQQ 持倉權重資料，支援按 QQQ weight 排序，並在卡片上動態顯示 QQQ / SPY 權重
- [x] 加入 Pagination 功能（每頁 25/50/100/全部，上下方雙導覽列）
- [x] 重整 `scripts/` 資料夾：移除一次性腳本，建立通用的 `add_companies.py`（支援 CLI 參數）與 `sync_index_data.py`（統一管理指數資料）
- [x] **資料來源標示**：強制要求 AI 在生成資料時提供實際可查證的來源 URL（如 SEC 10-K），並顯示於個別企業頁面。
