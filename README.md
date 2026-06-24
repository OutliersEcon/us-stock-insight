# 🗺️ US Stock Insight (美股業務透視)

**US Stock Insightp** 是一個由 AI Agent 驅動的專案，旨在為投資者提供標普 500 (SPY ETF) 成分股的深度業務解析。本專案會自動追蹤 SPY 的持倉變化，並利用 AI 技術分析每間公司的核心業務及其各個業務板塊對總收入的貢獻比例，最終透過 GitHub Pages 提供直觀、免費的靜態網頁供大眾查閱。

## ✨ 核心功能 (Features)

- **🔄 自動化持倉同步**：定期下載並解析 SPY ETF 的最新持倉清單，確保名單涵蓋美國最重要的核心企業。
- **🤖 AI 業務解析**：利用 AI Agent 自動檢索並總結每間公司的核心業務模式。
- **📊 營收結構拆解**：精確列出各個業務部門（Segments）對公司總收入的貢獻比例（例如：Apple 的 iPhone、Mac、Services 營收佔比）。
- **🌐 零成本託管**：完全基於 GitHub Pages 部署，前端採用靜態網站生成器，實現極速載入與零伺服器成本。
- **⏰ 定期更新**：透過 GitHub Actions 設定 Cron Job，實現數據的每週/每月自動更新。

## 🏗️ 系統架構 (Architecture)

本專案採用現代化的 Serverless 與靜態網站架構，主要分為三個模組：

### 1. 數據獲取與處理層 (Data Fetching & Processing)
- **SPY 持倉獲取器**：直接抓取 ETF 發行商 CSV獲取最新的 SPY 成分股權重與名單。
- **AI Agent 處理器**：
  - 使用 Python / Node.js 編寫腳本。
  - 整合 OpenAI API (或其他 LLM) 與財報數據源 (SEC EDGAR, 企業年報)。
  - 提取並結構化數據，生成統一格式的 JSON 檔案（包含公司簡介、業務板塊、營收佔比等）。

### 2. 自動化工作流 (Automation - GitHub Actions)
- 設定定時任務（Cron Jobs）。
- 工作流觸發後，依序執行：抓取持倉 -> 呼叫 AI Agent 更新缺失或過期的公司數據 -> 將更新後的 JSON 數據提交 (Commit) 到 Repo 中。

### 3. 前端展示層 (Frontend - GitHub Pages)
- 使用靜態網站生成器（如 Next.js, Astro, 或 Vue/Nuxt）。
- 讀取生成的 JSON 數據，渲染成視覺化的圖表（如圓餅圖、長條圖）與公司卡片。
- 每次數據更新或程式碼推送時，GitHub Actions 會自動 Build 並部署到 GitHub Pages。

🗺️ 開發路線圖 (Roadmap)
 建立基礎 GitHub 儲存庫與 README
 實作 SPY 持倉自動下載腳本
 開發 AI Agent 以結構化提取財報中的營收佔比
 建立前端 UI (包含搜尋、過濾、圓餅圖視覺化)
 整合 GitHub Actions 實現全自動化 CI/CD
 支援多國語言 (英文/繁體中文) 切換
