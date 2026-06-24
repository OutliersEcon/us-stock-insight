"""
generate_pages.py
=================
根據 data/processed/companies.json 批量生成 stocks/{TICKER}.html 個別企業頁面。

命名規則 (Ticker → Filename)
-----------------------------
- 一般 Ticker：直接使用大寫，例如 AAPL → AAPL.html
- 含「.」的 Ticker（如 BRK.B、BRK.A）：將「.」替換為「-」，例如 BRK.B → BRK-B.html
  - 理由：「.」在 URL 路徑中可能造成混淆，「-」是 URL 友善的分隔符號
- 含「/」的 Ticker：同樣替換為「-」
- 所有字母統一大寫

範例：
  AAPL    → stocks/AAPL.html
  BRK.B   → stocks/BRK-B.html
  BRK.A   → stocks/BRK-A.html
  GOOGL   → stocks/GOOGL.html
  GOOG    → stocks/GOOG.html
"""

import json
import os
import re

COMPANIES_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'companies.json')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'stocks')

SECTOR_COLORS = {
    "Technology": "#60a5fa",
    "Financials": "#34d399",
    "Healthcare": "#f472b6",
    "Consumer Discretionary": "#fb923c",
    "Consumer Staples": "#a78bfa",
    "Communication Services": "#facc15",
    "Energy": "#f87171",
}

PIE_PALETTE = [
    "#4f8ef7", "#7c3aed", "#22c55e", "#f59e0b",
    "#ef4444", "#06b6d4", "#ec4899", "#84cc16",
    "#f97316", "#8b5cf6", "#14b8a6", "#e11d48"
]

def ticker_to_filename(ticker: str) -> str:
    """將 Ticker 轉換為安全的檔案名稱（不含副檔名）。"""
    return re.sub(r'[./]', '-', ticker).upper()

def generate_page(company: dict) -> str:
    """生成單一企業的 HTML 頁面內容。"""
    ticker = company['ticker']
    filename = ticker_to_filename(ticker)
    name = company['name']
    sector = company['sector']
    description = company['description']
    weight = company['weight']
    segments = company['revenue_segments']
    sector_color = SECTOR_COLORS.get(sector, "#8892a4")

    # Pie chart data
    pie_labels = json.dumps([s['segment'] for s in segments])
    pie_data = json.dumps([s['percentage'] for s in segments])
    pie_colors = json.dumps(PIE_PALETTE[:len(segments)])

    # Segment rows HTML
    seg_rows = ""
    for i, s in enumerate(segments):
        color = PIE_PALETTE[i % len(PIE_PALETTE)]
        seg_rows += f"""
        <div class="seg-item">
          <div class="seg-header">
            <div class="seg-dot" style="background:{color}"></div>
            <span class="seg-name">{s['segment']}</span>
            <span class="seg-pct">{s['percentage']}%</span>
          </div>
          <div class="seg-bar-wrap">
            <div class="seg-bar" style="width:{s['percentage']}%;background:{color}"></div>
          </div>
          <p class="seg-desc">{s['description']}</p>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{ticker} · {name} | US Stock Insight</title>
  <meta name="description" content="{description[:120]}" />
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --bg: #0f1117; --surface: #1a1d27; --surface2: #22263a;
      --border: #2e3250; --accent: #4f8ef7; --accent2: #7c3aed;
      --text: #e2e8f0; --text-muted: #8892a4; --radius: 12px;
      --sector-color: {sector_color};
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; min-height: 100vh; }}

    header {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 0 24px; position: sticky; top: 0; z-index: 100; }}
    .header-inner {{ max-width: 1100px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; height: 60px; }}
    .back-link {{ display: flex; align-items: center; gap: 8px; text-decoration: none; color: var(--text-muted); font-size: 14px; transition: color .2s; }}
    .back-link:hover {{ color: var(--accent); }}
    .header-ticker {{ font-size: 16px; font-weight: 700; color: var(--text); }}

    .hero {{ max-width: 1100px; margin: 0 auto; padding: 40px 24px 0; }}
    .hero-top {{ display: flex; align-items: flex-start; gap: 20px; flex-wrap: wrap; margin-bottom: 24px; }}
    .ticker-big {{ background: linear-gradient(135deg, var(--accent), var(--accent2)); border-radius: 12px; padding: 12px 20px; font-size: 28px; font-weight: 800; color: #fff; letter-spacing: 1px; flex-shrink: 0; }}
    .hero-info {{ flex: 1; }}
    .hero-name {{ font-size: 22px; font-weight: 700; margin-bottom: 6px; }}
    .hero-meta {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 10px; }}
    .badge {{ border-radius: 6px; padding: 4px 10px; font-size: 12px; font-weight: 600; }}
    .badge-sector {{ background: var(--surface2); color: var(--sector-color); border: 1px solid var(--sector-color)40; }}
    .badge-weight {{ background: var(--surface2); color: var(--text-muted); border: 1px solid var(--border); }}
    .hero-desc {{ font-size: 15px; color: var(--text-muted); line-height: 1.7; max-width: 700px; }}

    .content {{ max-width: 1100px; margin: 0 auto; padding: 32px 24px 60px; display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
    @media (max-width: 768px) {{ .content {{ grid-template-columns: 1fr; }} }}

    .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; }}
    .card-title {{ font-size: 16px; font-weight: 700; margin-bottom: 20px; display: flex; align-items: center; gap: 8px; }}
    .card-title-icon {{ font-size: 18px; }}

    .chart-wrap {{ position: relative; height: 280px; display: flex; align-items: center; justify-content: center; }}

    .seg-item {{ margin-bottom: 16px; }}
    .seg-item:last-child {{ margin-bottom: 0; }}
    .seg-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }}
    .seg-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
    .seg-name {{ flex: 1; font-size: 14px; font-weight: 600; }}
    .seg-pct {{ font-size: 15px; font-weight: 700; color: var(--accent); }}
    .seg-bar-wrap {{ height: 6px; background: var(--surface2); border-radius: 3px; overflow: hidden; margin-bottom: 6px; }}
    .seg-bar {{ height: 100%; border-radius: 3px; transition: width .6s ease; }}
    .seg-desc {{ font-size: 12px; color: var(--text-muted); padding-left: 18px; }}

    .note-card {{ grid-column: 1 / -1; }}
    .note {{ background: var(--surface2); border-left: 3px solid var(--accent); border-radius: 0 8px 8px 0; padding: 12px 16px; font-size: 13px; color: var(--text-muted); line-height: 1.6; }}

    footer {{ border-top: 1px solid var(--border); padding: 20px 24px; text-align: center; color: var(--text-muted); font-size: 12px; }}
    footer a {{ color: var(--accent); text-decoration: none; }}
  </style>
</head>
<body>

<header>
  <div class="header-inner">
    <a class="back-link" href="../index.html">← 返回總覽</a>
    <div class="header-ticker">{ticker}</div>
  </div>
</header>

<div class="hero">
  <div class="hero-top">
    <div class="ticker-big">{ticker}</div>
    <div class="hero-info">
      <div class="hero-name">{name}</div>
      <div class="hero-meta">
        <span class="badge badge-sector">{sector}</span>
        <span class="badge badge-weight">SPY 權重 {weight:.2f}%</span>
      </div>
      <p class="hero-desc">{description}</p>
    </div>
  </div>
</div>

<div class="content">
  <!-- Pie Chart -->
  <div class="card">
    <div class="card-title"><span class="card-title-icon">🥧</span> 營收結構圓餅圖</div>
    <div class="chart-wrap">
      <canvas id="pieChart"></canvas>
    </div>
  </div>

  <!-- Segments Detail -->
  <div class="card">
    <div class="card-title"><span class="card-title-icon">📋</span> 業務板塊詳細拆解</div>
    {seg_rows}
  </div>

  <!-- Note -->
  <div class="card note-card">
    <div class="note">
      ⚠️ 本頁面的營收佔比數據基於公司最新年報及公開財報資料，僅供參考。各業務板塊的實際佔比可能因會計年度、匯率及業務調整而有所差異。本站資訊不構成任何投資建議。
    </div>
  </div>
</div>

<footer>
  <p>資料來源：公司年報、SEC EDGAR &nbsp;|&nbsp; <a href="../index.html">返回 US Stock Insight 首頁</a></p>
</footer>

<script>
  const ctx = document.getElementById('pieChart').getContext('2d');
  new Chart(ctx, {{
    type: 'doughnut',
    data: {{
      labels: {pie_labels},
      datasets: [{{
        data: {pie_data},
        backgroundColor: {pie_colors},
        borderColor: '#0f1117',
        borderWidth: 2,
        hoverOffset: 8
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{
          position: 'bottom',
          labels: {{
            color: '#8892a4',
            font: {{ size: 11 }},
            padding: 12,
            boxWidth: 12
          }}
        }},
        tooltip: {{
          callbacks: {{
            label: ctx => ` ${{ctx.label}}: ${{ctx.parsed}}%`
          }}
        }}
      }},
      cutout: '55%'
    }}
  }});
</script>
</body>
</html>"""
    return html


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(COMPANIES_FILE, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    generated = []
    for company in companies:
        filename = ticker_to_filename(company['ticker'])
        html = generate_page(company)
        output_path = os.path.join(OUTPUT_DIR, f"{filename}.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        generated.append(f"  {company['ticker']:10} → stocks/{filename}.html")
        print(f"✓ Generated: stocks/{filename}.html")

    print(f"\n✅ 共生成 {len(generated)} 個企業頁面")
    print("\n命名規則說明：")
    print("  一般 Ticker：直接使用大寫（AAPL → AAPL.html）")
    print("  含「.」的 Ticker：「.」替換為「-」（BRK.B → BRK-B.html）")


if __name__ == '__main__':
    main()
