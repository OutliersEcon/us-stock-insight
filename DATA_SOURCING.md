# 📚 資料獲取知識庫 (Data Sourcing Guide)

> **核心原則**：本專案嚴格禁止 AI 根據自身訓練知識估算任何財務數據。所有業務板塊佔比、營收數字及相關描述，必須基於可查證的真實來源（SEC EDGAR 申報文件、公司官方 IR 頁面等）。若無法取得真實來源，寧可標記為「資料缺失」，也不允許 AI 捏造數字。

---

## 目錄

1. [資料品質分級](#1-資料品質分級)
2. [SEC EDGAR API 技術指南](#2-sec-edgar-api-技術指南)
3. [可行的資料獲取方法](#3-可行的資料獲取方法)
4. [不可行或受限的方法](#4-不可行或受限的方法)
5. [特殊企業處理方式](#5-特殊企業處理方式)
6. [User-Agent 設定規範](#6-user-agent-設定規範)
7. [常見錯誤與排查](#7-常見錯誤與排查)
8. [已知 CIK 快速參考](#8-已知-cik-快速參考)

---

## 1. 資料品質分級

本專案使用 `data_quality` 欄位標示每間企業資料的可信度：

| 等級 | 值 | 說明 | 允許條件 |
|---|---|---|---|
| **真實數據** | `real_data` | 從 SEC EDGAR 10-Q 或 10-K 申報文件中提取 | 成功抓取財報文字後由 AI 結構化 |
| **估算數據** | `estimated` | AI 根據自身知識估算 | **原則上不允許**，僅在非美國上市企業（如 TSM、FUTU）且無其他可靠來源時例外 |

> **重要**：`estimated` 標記代表資料可靠性存疑，應盡快以真實財報數據替換。若 `ai_agent_parser.py` 輸出 `data_quality=estimated`，表示 Phase 1 失敗，需排查原因（見[第 7 節](#7-常見錯誤與排查)）。

---

## 2. SEC EDGAR API 技術指南

### 2.1 可用端點總覽

SEC EDGAR 提供多個 API 端點，各端點的可訪問性在不同環境下有所差異：

| 端點 | 用途 | Manus 沙盒可訪問 | 備註 |
|---|---|---|---|
| `data.sec.gov/submissions/CIK{cik}.json` | 查詢企業申報歷史 | ✅ 可訪問 | 需要先知道 CIK |
| `efts.sec.gov/LATEST/search-index` | 全文搜尋申報文件 | ✅ 可訪問 | 可用於查詢 CIK |
| `www.sec.gov/Archives/edgar/data/` | 下載申報原始文件 | ✅ 可訪問 | 需要 CIK 和 accession number |
| `www.sec.gov/files/company_tickers.json` | ticker→CIK 對照表 | ❌ 403 Forbidden | 沙盒 IP 被封鎖 |
| `www.sec.gov/cgi-bin/browse-edgar` | HTML 搜尋頁面 | ❌ 403 Forbidden | 沙盒 IP 被封鎖 |
| `efts.sec.gov/LATEST/search-index` | 全文搜尋（帶 dateRange） | ⚠️ 間歇性 500 | 不建議使用 dateRange 參數 |

### 2.2 CIK 查詢方法（推薦）

**使用 `efts.sec.gov` Full-Text Search API**：

```python
import requests, re

SEC_HEADERS = {"User-Agent": "us-stock-insight admin@outliersecon.com"}

def get_cik_from_ticker(ticker: str) -> str | None:
    ticker_upper = ticker.upper()
    # 搜尋 ticker 在 10-Q 申報中的出現
    url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker_upper}%22&forms=10-Q"
    resp = requests.get(url, headers=SEC_HEADERS, timeout=15)
    data = resp.json()
    buckets = data.get("aggregations", {}).get("entity_filter", {}).get("buckets", [])

    # 精確匹配：ticker 出現在括號中，格式為 "COMPANY (TICKER) (CIK XXXXXXXXXX)"
    for bucket in buckets:
        display_name = bucket.get("key", "")
        if f"({ticker_upper})" in display_name or f"({ticker_upper}," in display_name:
            cik_match = re.search(r"CIK (\d+)", display_name)
            if cik_match:
                return cik_match.group(1).zfill(10)
    return None
```

**回傳格式範例**：
- `"MICROSOFT CORP  (MSFT)  (CIK 0000789019)"` → CIK: `0000789019`
- `"Unusual Machines, Inc.  (UMAC)  (CIK 0001956955)"` → CIK: `0001956955`

### 2.3 取得最新申報連結

取得 CIK 後，透過 `data.sec.gov/submissions/` 查詢最新申報：

```python
def get_latest_filing(cik: str, form_type: str = "10-Q") -> dict | None:
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=SEC_HEADERS, timeout=15)
    data = resp.json()
    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    accessions = filings.get("accessionNumber", [])
    periods = filings.get("reportDate", [])

    for i, form in enumerate(forms):
        if form == form_type:
            accession = accessions[i].replace("-", "")
            cik_int = int(cik)
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/"
            return {"filing_url": filing_url, "period": periods[i]}
    return None
```

**注意**：`data.sec.gov/submissions/CIK{cik}.json` 的 CIK 必須是 **10 位數字**（前面補零），例如 `CIK0000789019`。

### 2.4 下載申報文件純文字

```python
def fetch_filing_text(filing_url: str, max_chars: int = 8000) -> str:
    # 先取得 index.json，找出主要 .htm 文件
    index_url = filing_url + "index.json"
    resp = requests.get(index_url, headers=SEC_HEADERS, timeout=15)
    files = resp.json().get("directory", {}).get("item", [])

    main_doc = None
    for f in files:
        name = f.get("name", "").lower()
        # 選取主文件：.htm 結尾，不是 exhibit（ex）也不是 R 開頭的表格
        if name.endswith(".htm") and not name.startswith("r") and "ex" not in name:
            main_doc = filing_url + f["name"]
            break

    if not main_doc:
        return ""

    doc_resp = requests.get(main_doc, headers=SEC_HEADERS, timeout=20)
    # 移除 HTML 標籤，壓縮空白
    text = re.sub(r"<[^>]+>", " ", doc_resp.text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]
```

---

## 3. 可行的資料獲取方法

### 方法 A：SEC EDGAR（美國上市企業，首選）

**適用範圍**：所有在美國交易所（NYSE、NASDAQ）上市的企業。

**完整流程**：
1. 用 `efts.sec.gov` 查詢 CIK（見 2.2）
2. 用 `data.sec.gov/submissions/CIK{cik}.json` 取得最新 10-Q 或 10-K 連結（見 2.3）
3. 下載申報文件純文字（見 2.4）
4. 將純文字交給 AI 結構化分析

**優先順序**：10-Q（季報）> 10-K（年報）

**Sources 記錄規範**：
- 必須記錄 SEC EDGAR 搜尋頁面 URL（永遠有效）：
  `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_int}&type=10-Q&dateb=&owner=include&count=5`
- 若成功下載文件，額外記錄文件直接 URL：
  `https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/`

### 方法 B：公司官方 IR 頁面（人工更新）

**適用範圍**：任何企業，尤其是非美國上市企業。

**流程**：
1. 訪問公司 Investor Relations 頁面（通常在 `ir.{company}.com` 或 `{company}.com/investors`）
2. 下載最新年報（Annual Report）或季報（Quarterly Earnings Release）
3. 手動提取業務板塊數字
4. 直接編輯 `companies.json`，填入真實數字和來源 URL

**適用企業範例**：
- TSM（台積電）：https://investor.tsmc.com/
- FUTU（富途控股）：https://ir.futuholdings.com/

### 方法 C：公司 Earnings Press Release（人工更新）

**適用範圍**：財報發布後希望快速更新的企業。

**流程**：
1. 在公司 IR 頁面或 PR Newswire 找到最新 Earnings Release PDF
2. 提取業務板塊數字
3. 記錄 PDF 的直接 URL 作為 source

---

## 4. 不可行或受限的方法

### ❌ 方法：AI 根據自身知識估算

**為何禁止**：
- AI 訓練數據有截止日期，無法反映最新財報數字
- AI 可能捏造不存在的業務板塊或百分比
- AI 生成的 URL 可能是幻覺（hallucination），無法實際訪問
- 違反本專案「資料可查證」的核心原則

**識別方式**：`data_quality: "estimated"` 且 `sources` 中無實際文件 URL。

**處理方式**：立即重新執行 `ai_agent_parser.py --force {TICKER}`，排查 SEC EDGAR 訪問問題。

---

### ❌ 方法：`www.sec.gov/files/company_tickers.json`

**問題**：Manus 沙盒 IP 被 `www.sec.gov` 封鎖，回傳 `403 Forbidden`。

**替代方案**：使用 `efts.sec.gov/LATEST/search-index`（見 2.2）。

**驗證測試**：
```bash
# 應回傳 403（沙盒環境）
curl -s -o /dev/null -w "%{http_code}" \
  -H "User-Agent: test admin@test.com" \
  "https://www.sec.gov/files/company_tickers.json"

# 應回傳 200（可正常使用）
curl -s -o /dev/null -w "%{http_code}" \
  -H "User-Agent: test admin@test.com" \
  "https://efts.sec.gov/LATEST/search-index?q=%22MSFT%22&forms=10-Q"
```

---

### ❌ 方法：`www.sec.gov/cgi-bin/browse-edgar`（作為 API）

**問題**：同樣被沙盒 IP 封鎖，回傳 `403 Forbidden`。

**注意**：此 URL 仍可作為 `sources` 中的參考連結（供人工查閱），但不能用於程式化抓取。

---

### ⚠️ 方法：`efts.sec.gov` 帶 `dateRange` 參數

**問題**：加入 `dateRange=custom&startdt=...&enddt=...` 參數時，偶爾回傳 `500 Internal Server Error`。

**建議**：不使用 `dateRange` 參數，直接搜尋 ticker，再從結果中取得最新申報。

---

### ⚠️ 方法：Yahoo Finance / Bloomberg / 財經新聞網站

**問題**：
- 資料通常為摘要，缺乏業務板塊細節
- 部分網站有反爬蟲機制
- 數字可能已被四捨五入或重新分類，與原始財報不符

**建議**：僅作為輔助參考，不作為主要資料來源。

---

## 5. 特殊企業處理方式

### 5.1 非美國上市企業（`NON_SEC_TICKERS`）

目前標記為非 SEC 企業的 Ticker：

| Ticker | 公司 | 上市地點 | 建議資料來源 |
|---|---|---|---|
| `TSM` | 台積電 | 台灣證交所 / NYSE ADR | https://investor.tsmc.com/ |
| `FUTU` | 富途控股 | NASDAQ（但主要業務在中國） | https://ir.futuholdings.com/ |

**處理方式**：`ai_agent_parser.py` 會跳過 SEC EDGAR 查詢，直接進入 AI 分析（`data_quality: estimated`）。建議人工更新這些企業的資料。

### 5.2 含特殊字元的 Ticker

| Ticker | HTML 檔案名 | 說明 |
|---|---|---|
| `BRK.B` | `BRK-B.html` | `.` 替換為 `-` |
| `BRK.A` | `BRK-A.html` | `.` 替換為 `-` |

**SEC EDGAR 查詢**：使用原始 ticker（如 `BRK-B`）查詢，SEC 系統可正確識別。

### 5.3 雙重上市企業（如 GOOGL / GOOG）

GOOGL 和 GOOG 共用同一份 SEC 申報（CIK 相同）。更新時只需更新其中一個，另一個可手動同步。

---

## 6. User-Agent 設定規範

SEC EDGAR 對 User-Agent 有嚴格要求，不符合規範的請求會被封鎖。

### 6.1 規範格式

```
{app-name} {contact-email}
```

**範例**：
```
us-stock-insight admin@outliersecon.com
```

### 6.2 已知封鎖情況

| User-Agent 特徵 | 結果 | 說明 |
|---|---|---|
| 包含 `github.io` 域名的 email | ❌ 403 | SEC 封鎖 GitHub Pages 域名 |
| 不含 email 地址 | ❌ 403 | SEC 要求必須有聯絡方式 |
| `python-requests/x.x.x` 預設值 | ❌ 403 | 未提供聯絡方式 |
| 含 `.com` 域名的普通 email | ✅ 200 | 正常訪問 |
| 含 `.org` 域名的 email | ✅ 200 | 正常訪問 |

### 6.3 腳本中的設定

`ai_agent_parser.py` 中的 `SEC_HEADERS` 設定：

```python
SEC_HEADERS = {
    "User-Agent": "us-stock-insight admin@outliersecon.com"
}
```

> **注意**：若更換 email 地址，請確保使用普通 `.com` 或 `.org` 域名，避免使用 `github.io`、`localhost` 等特殊域名。

---

## 7. 常見錯誤與排查

### 錯誤：`CIK not found on SEC EDGAR`

**可能原因**：
1. User-Agent 被封鎖（最常見）→ 檢查 `SEC_HEADERS` 中的 email 域名
2. Ticker 不在 SEC EDGAR（非美國上市）→ 加入 `NON_SEC_TICKERS`
3. `efts.sec.gov` 暫時不可用 → 等待後重試

**排查步驟**：
```bash
# 測試 User-Agent 是否可訪問 efts.sec.gov
python3 -c "
import requests
headers = {'User-Agent': 'us-stock-insight admin@outliersecon.com'}
resp = requests.get('https://efts.sec.gov/LATEST/search-index?q=%22MSFT%22&forms=10-Q', headers=headers, timeout=10)
print('Status:', resp.status_code)
"
```

---

### 錯誤：`data_quality=estimated`（意外出現）

**原因**：Phase 1 未能取得財報文字，AI 改用自身知識估算。

**處理方式**：
1. 確認 Ticker 是否在 `NON_SEC_TICKERS` 中（若是，屬正常行為）
2. 執行上述 User-Agent 測試
3. 手動確認 CIK：
   ```bash
   curl -s -H "User-Agent: us-stock-insight admin@outliersecon.com" \
     "https://efts.sec.gov/LATEST/search-index?q=%22{TICKER}%22&forms=10-Q" \
     | python3 -c "import json,sys; d=json.load(sys.stdin); print([b['key'] for b in d['aggregations']['entity_filter']['buckets'][:3]])"
   ```

---

### 錯誤：`Filing text fetch failed`

**可能原因**：
1. 申報文件的主要 `.htm` 文件命名不符合預期格式
2. 文件過大，下載超時

**處理方式**：
- 手動訪問 `filing_url + "index.json"` 查看文件清單
- 調整 `fetch_filing_text()` 中的文件選取邏輯

---

### 錯誤：`403 Forbidden` on `www.sec.gov`

**原因**：Manus 沙盒 IP 被 `www.sec.gov` 封鎖。

**處理方式**：確認所有 CIK 查詢和申報清單查詢均使用 `efts.sec.gov` 或 `data.sec.gov`，而非 `www.sec.gov`。

> **例外**：`www.sec.gov/Archives/edgar/data/` 的文件下載 URL 不受此限制，可正常訪問。

---

## 8. 已知 CIK 快速參考

以下為常用企業的 CIK，可直接使用，無需查詢：

| Ticker | 公司名稱 | CIK |
|---|---|---|
| AAPL | Apple Inc. | 0000320193 |
| MSFT | Microsoft Corporation | 0000789019 |
| AMZN | Amazon.com Inc. | 0001018724 |
| GOOGL | Alphabet Inc. | 0001652044 |
| NVDA | NVIDIA Corporation | 0001045810 |
| META | Meta Platforms Inc. | 0001326801 |
| TSLA | Tesla Inc. | 0001318605 |
| AVGO | Broadcom Inc. | 0001730168 |
| UMAC | Unusual Machines Inc. | 0001956955 |
| IBKR | Interactive Brokers Group | 0001381197 |

> **說明**：此表格僅供快速參考，實際執行時 `ai_agent_parser.py` 仍會透過 `efts.sec.gov` 動態查詢 CIK，確保資料最新。

---

*本文件由 us-stock-insight 專案維護，記錄資料獲取的實際經驗與技術細節。如發現新的可行或不可行方法，請更新此文件。*
