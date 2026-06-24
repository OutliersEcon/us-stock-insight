# 🗺️ US Stock Insight (美股業務透視)

**US Stock Insight** 是一個由 AI Agent 驅動的開源專案，旨在為投資者提供美股核心企業的深度業務解析。本專案不僅自動追蹤標普 500 (SPY ETF) 的持倉變化，亦支援收錄不在 S&P 500 指數內的精選企業。透過 AI 技術分析每間公司的核心業務及其各個業務板塊對總收入的貢獻比例，最終透過 GitHub Pages 提供直觀、免費的靜態網頁供大眾查閱。

🌐 **網站入口**：[US Stock Insight GitHub Pages](https://outliersecon.github.io/us-stock-insight/) *(請確認 GitHub Pages 已在倉庫設定中啟用並指向 `main` 分支)*

---

## ✨ 核心功能 (Features)

- **🔄 自動化持倉同步**：定期下載並解析 SPY ETF 的最新持倉清單，目前已收錄 **123 間** 核心企業（包含 S&P 500 成分股及精選自選企業）。
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
| `add_companies.py` | **通用企業新增工具**：透過 AI 為任意 Ticker 清單生成業務描述與營收結構，支援命令列參數 |
| `sync_index_data.py` | **指數資料同步工具**：統一管理 SPY/QQQ 持倉權重、`in_sp500` 與 `nasdaq100` 欄位的更新 |
| `ai_agent_parser.py` | **真實財報抓取器**：供 Manus Scheduled Task 呼叫，從 SEC EDGAR 抓取真實財報文字並交由 AI 分析 |
| `generate_update_log.py` | 從 `companies.json` 自動生成 `data/update_log.json`，供 AI 更新器判斷哪些企業需要更新 |
| `generate_pages.py` | 根據 `companies.json` 批量生成所有 HTML 頁面（`index.html` 與 `stocks/*.html`）|

### 2. 資料來源可信度政策 (Source Credibility Policy)

> ⛔ **嚴格禁止**：AI 在任何情況下均不得根據自身訓練知識估算業務板塊佔比、營收數字或任何財務數據。所有數字必須來自可查證的真實來源（SEC EDGAR 申報文件、公司官方 IR 頁面等）。若無法取得真實來源，應將 `data_quality` 標記為 `estimated` 並立即排查原因，而非接受估算數據作為最終結果。

本專案堅持「**不允許 AI 捏造來源與數字**」的原則，`ai_agent_parser.py` 採用兩階段流程：
1. **Phase 1 (真實財報抓取)**：先從 SEC EDGAR 查詢企業 CIK，抓取最新 10-Q 或 10-K 申報文件的純文字內容，並記錄實際訪問的 URL。
2. **Phase 2 (AI 結構化分析)**：將抓取到的真實財報文字交給 AI，AI 僅作為「文字理解與結構化」工具，提取業務板塊佔比並生成繁體中文描述。

**資料來源標示**：
- `sources`：記錄實際訪問過的來源 URL 清單。若無法取得直接文件，則使用 SEC EDGAR 搜尋頁面（永遠有效的 URL）。
- `data_period`：記錄資料所屬的財報期間（如 `FY2027 Q1 (截至 2026 年 4 月 26 日)`）。
- `data_quality`：若成功抓取財報文字，標示為 `real_data`；若無法取得（如非美國上市企業），則標示為 `estimated`。

**延伸閱讀**：資料獲取的詳細技術指南、SEC EDGAR API 端點說明、已知限制與排查方法，請參閱 **[📚 DATA_SOURCING.md](./DATA_SOURCING.md)**。

### 3. 前端展示與靜態頁面生成 (Frontend Generation)

- **頁面生成器** (`scripts/generate_pages.py`)：讀取 `companies.json`，透過 Python 腳本動態生成：
  1. `index.html`：總覽主頁，UI 樣式與 DOM 結構定義於此。
  2. `stocks/*.html`：每間公司的獨立詳細頁面，包含 Chart.js 圓餅圖與最後更新日期。
- **前端邏輯分離** (`app.js`)：
  主頁的所有互動邏輯皆包含於單一 `app.js` 檔案中。雖然未拆分為多個實體檔案，但程式碼內部已透過註解分為以下邏輯區塊：
  - **常數定義**：`SECTOR_ZH`（行業中英對照）、`SEARCH_ALIASES`（公司別名字典）。
  - **狀態管理**：管理 `companies`、`activeSector`、`activeIndex`、`sortBy`、`searchQuery`、`currentPage` 等全域狀態。
  - **搜尋與排序邏輯**：`matchSearch()`（支援 Ticker、名稱、別名、行業）、`sortCompanies()`（非 S&P 500 企業固定排最後）。
  - **渲染邏輯**：`renderCard()`（單一企業卡片）、`renderPagination()`（分頁導覽列）、`renderGrid()`（整合篩選與分頁的網格渲染）。
  - **事件監聽**：`initEvents()` 綁定所有 UI 互動（搜尋、點擊篩選、切換分頁等）。
- **多 Ticker 命名規則**：
  - **一般 Ticker**：直接使用大寫字母，例如 `AAPL` → `AAPL.html`。
  - **含特殊字元 (`.`, `/`) 的 Ticker**：將特殊字元替換為 `-`，例如 `BRK.B` 轉換為 `BRK-B.html`。

### 4. 職責分離的自動化工作流 (Separation of Duties)

為確保資料更新的穩定性與可靠性，本專案將「網站完整性檢查」與「財報數據更新」拆分為兩個獨立的流程：

**A. GitHub Actions (網站完整性檢查與部署)**
- **負責**：每週一自動執行（`.github/workflows/data-update.yml`）。
- **內容**：檢查 `companies.json` 與 HTML 頁面是否同步，重新計算 `update_log.json` 中的 `days_since_update`，並重新生成所有 HTML 頁面。
- **限制**：**不呼叫任何 AI API**，不抓取外部財報數據。

**B. Manus Scheduled Task (真實財報數據更新)**
- **負責**：由用戶在 Manus 平台設定的定期任務。
- **內容**：執行 `scripts/ai_agent_parser.py`，找出 `last_updated` 超過 30 天的企業，從 SEC EDGAR 抓取真實財報並交由 AI 分析，更新 `companies.json`。
- **優勢**：可利用 Manus 的網路訪問能力與 API 資源，專注於高成本的數據抓取與分析工作。

---

## 📋 操作指南 (Operations Guide)

### 設定 Manus Scheduled Task（財報更新）

若要自動更新過期的企業財報數據，請在 Manus 平台設定 Scheduled Task：
1. 開啟 Manus，使用 `manus-config schedule` 技能。
2. 設定一個每週執行的任務（例如每週三）。
3. 任務指令：
   ```bash
   cd /home/ubuntu/us-stock-insight
   python3 scripts/ai_agent_parser.py --regenerate-pages
   git add data/ stocks/ index.html
   git commit -m "update: auto-fetch latest financial data via Manus"
   git push origin main
   ```

### 新增企業

```bash
# 新增一間或多間自選企業（AI 自動生成資料）
python3 scripts/add_companies.py TICKER1 TICKER2

# 新增 S&P 500 成員（加上 --sp500 旗標，會設定 in_sp500: true）
python3 scripts/add_companies.py --sp500 NEWSTOCK

# 從文字檔批量新增（每行一個 Ticker，# 開頭為注釋行）
python3 scripts/add_companies.py --file tickers.txt

# 新增後，重新生成追蹤日誌與所有 HTML 頁面
python3 scripts/generate_update_log.py
python3 scripts/generate_pages.py
```

### 更新企業資料

**方式一：手動觸發真實財報抓取腳本（適合批量更新）**

```bash
# 更新所有超過 30 天未更新的企業
python3 scripts/ai_agent_parser.py --regenerate-pages

# 強制更新特定企業（忽略 30 天限制）
python3 scripts/ai_agent_parser.py --force AAPL MSFT --regenerate-pages
```

**方式二：人工更新（推薦用於重要企業，確保來源真實）**

1. 訪問公司官方財報（SEC EDGAR、公司 IR 頁面、CFO Commentary PDF）
2. 直接編輯 `data/processed/companies.json` 中對應企業的欄位：
   - `description`：業務描述（繁體中文）
   - `revenue_segments`：業務板塊清單（按百分比降冪排列）
   - `data_period`：資料時間性（如 `"FY2027 Q1 (截至 2026 年 4 月 26 日)"`）
   - `sources`：實際訪問過的來源 URL 清單
   - `last_updated`：更新為今天日期（`YYYY-MM-DD` 格式）
3. 重新生成頁面並提交：

```bash
python3 scripts/generate_update_log.py
python3 scripts/generate_pages.py
git add data/ stocks/ && git commit -m "update: manually update {TICKER} with FY20XX QX data"
git push origin main
```

---

## 📂 目錄結構 (Directory Structure)

```text
us-stock-insight/
├── .github/workflows/
│   └── data-update.yml        # GitHub Actions 完整性檢查與部署腳本
├── data/
│   ├── raw/                   # 存放原始抓取的 SPY Excel/CSV 資料
│   ├── processed/             # 存放 AI 處理後的 companies.json
│   └── update_log.json        # 自動生成的更新追蹤日誌
├── scripts/
│   ├── add_companies.py       # 通用企業新增工具（支援任意 Ticker，可重複使用）
│   ├── sync_index_data.py     # SPY/QQQ 持倉權重與指數成員資料同步工具
│   ├── fetch_spy_holdings.py  # 抓取 SPY 持倉的 Python 腳本
│   ├── ai_agent_parser.py     # 真實財報抓取器（SEC EDGAR + AI 分析，供 Manus 呼叫）
│   ├── generate_update_log.py # 生成更新追蹤日誌的腳本
│   └── generate_pages.py      # 根據 JSON 批量生成 HTML 頁面的腳本
├── stocks/                    # 動態生成的個別企業 HTML 頁面 (例如 AAPL.html)
├── index.html                 # 網站主頁 UI 結構
├── app.js                     # 網站主頁前端互動邏輯 (搜尋/排序/篩選)
├── requirements.txt           # Python 依賴清單
├── DATA_SOURCING.md           # 資料獲取知識庫：SEC EDGAR API 指南、可行與不可行方法、排查指南
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
- [x] 大幅擴充收錄企業範圍（共 123 間，包含 S&P 500、Nasdaq 100 與自選企業）
- [x] 前端重構：加入排序功能、指數 Toggle、優化搜尋體驗（支援別名搜尋）
- [x] 支援收錄非 S&P 500 之精選企業，並完善前端排序與標籤邏輯
- [x] 加入 `escapeHtml()` 將所有來自 JSON 的動態內容進行 HTML 變數轉義，防止 XSS
- [x] 加入 QQQ 持倉權重資料，支援按 QQQ weight 排序
- [x] 加入 Pagination 功能（每頁 25/50/100/全部，上下方雙導覽列）
- [x] **工作流職責分離**：GitHub Actions 專注於完整性檢查與部署；財報數據更新交由 Manus Scheduled Task 負責。
- [x] **資料來源可信度政策**：重新設計 `ai_agent_parser.py` 為兩階段流程（SEC EDGAR 抓取真實財報文字 + AI 分析），杜絕 AI 捏造來源與數字。
