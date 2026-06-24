/**
 * app.js — US Stock Insight 主頁互動邏輯
 * ==========================================
 * 功能：
 *  - 從 companies.json 動態載入企業資料
 *  - 行業篩選（英文 + 中文雙語）
 *  - 指數篩選 toggle（S&P 500 / Nasdaq 100）
 *  - 排序（SPY 權重 / Ticker 代號 / 公司名稱）
 *  - 智慧搜尋（支援 Ticker、公司名稱、中文別名、行業）
 *  - 動態渲染公司卡片
 */

'use strict';

// ── 行業英文 → 中文對照表
const SECTOR_ZH = {
  'Technology':               '科技',
  'Financials':               '金融',
  'Healthcare':               '醫療保健',
  'Consumer Discretionary':   '非必需消費',
  'Consumer Staples':         '必需消費',
  'Communication Services':   '通訊服務',
  'Energy':                   '能源',
  'Industrials':              '工業',
  'Materials':                '原材料',
  'Real Estate':              '房地產',
  'Utilities':                '公用事業',
};

// ── 公司名稱別名對照表（用於搜尋，解決 "Google" 找不到 GOOGL 的問題）
const SEARCH_ALIASES = {
  'GOOGL': ['google', 'alphabet', 'goog'],
  'GOOG':  ['google', 'alphabet', 'googl'],
  'META':  ['facebook', 'fb', 'instagram', 'whatsapp'],
  'AMZN':  ['amazon', 'aws'],
  'MSFT':  ['microsoft', 'azure', 'office', 'windows'],
  'AAPL':  ['apple', 'iphone', 'ipad', 'mac'],
  'NVDA':  ['nvidia', 'geforce'],
  'TSLA':  ['tesla', 'elon'],
  'AVGO':  ['broadcom', 'vmware'],
  'BRK-B': ['berkshire', 'buffett', 'brk', 'brk.b', 'brk.a'],
  'JPM':   ['jpmorgan', 'chase'],
  'WMT':   ['walmart', "sam's club"],
  'XOM':   ['exxon', 'mobil'],
  'JNJ':   ['johnson'],
  'LLY':   ['lilly', 'eli lilly', 'mounjaro', 'zepbound'],
  'V':     ['visa'],
  'MA':    ['mastercard'],
  'COST':  ['costco'],
  'NFLX':  ['netflix'],
  'GS':    ['goldman', 'sachs'],
  'MRK':   ['merck'],
  'ABBV':  ['abbvie', 'humira'],
  'BAC':   ['bank of america', 'bofa'],
  'UNH':   ['unitedhealth', 'united health'],
  'HD':    ['home depot'],
  'PG':    ['procter', 'gamble', 'p&g'],
  'KO':    ['coca cola', 'coca-cola', 'coke'],
  'CVX':   ['chevron'],
  'INTC':  ['intel'],
  'CSCO':  ['cisco'],
  'TXN':   ['texas instruments'],
  'QCOM':  ['qualcomm'],
  'AMD':   ['amd', 'radeon', 'ryzen', 'epyc'],
  'PLTR':  ['palantir'],
  'DELL':  ['dell'],
  'IBM':   ['ibm', 'international business machines'],
  'RTX':   ['raytheon'],
  'GE':    ['general electric'],
  'CAT':   ['caterpillar'],
  'BA':    ['boeing'],
  'LMT':   ['lockheed', 'martin'],
  'HON':   ['honeywell'],
  'UNP':   ['union pacific'],
  'DE':    ['deere', 'john deere'],
  'ETN':   ['eaton'],
  'PFE':   ['pfizer'],
  'ABT':   ['abbott'],
  'TMO':   ['thermo fisher'],
  'DHR':   ['danaher'],
  'ISRG':  ['intuitive surgical', 'da vinci'],
  'GILD':  ['gilead'],
  'AMGN':  ['amgen'],
  'VRTX':  ['vertex'],
  'SYK':   ['stryker'],
  'BMY':   ['bristol myers', 'bristol-myers'],
  'CVS':   ['cvs health'],
  'COP':   ['conocophillips'],
  'XOM':   ['exxon', 'exxonmobil'],
  'NEE':   ['nextera'],
  'BLK':   ['blackrock'],
  'BX':    ['blackstone'],
  'SCHW':  ['schwab', 'charles schwab'],
  'AXP':   ['american express', 'amex'],
  'COF':   ['capital one'],
  'PGR':   ['progressive'],
  'SPGI':  ['s&p global', 'sp global'],
  'CME':   ['cme group', 'chicago mercantile'],
  'MS':    ['morgan stanley'],
  'C':     ['citigroup', 'citi'],
  'WFC':   ['wells fargo'],
  'MCD':   ["mcdonald's", 'mcdonalds'],
  'SBUX':  ['starbucks'],
  'TJX':   ['tjx', 't.j. maxx', 'marshalls'],
  'LOW':   ["lowe's", 'lowes'],
  'BKNG':  ['booking', 'priceline'],
  'UBER':  ['uber'],
  'MO':    ['altria', 'marlboro'],
  'PM':    ['philip morris'],
  'PEP':   ['pepsi', 'pepsico', 'frito'],
  'KO':    ['coca cola', 'coke'],
  'WMT':   ['walmart'],
  'COST':  ['costco'],
  'CRM':   ['salesforce'],
  'NOW':   ['servicenow'],
  'ADBE':  ['adobe'],
  'INTU':  ['intuit', 'turbotax', 'quickbooks'],
  'ADP':   ['adp', 'automatic data'],
  'SNPS':  ['synopsys'],
  'CDNS':  ['cadence'],
  'PANW':  ['palo alto'],
  'CRWD':  ['crowdstrike'],
  'FTNT':  ['fortinet'],
  'ANET':  ['arista'],
  'TMUS':  ['t-mobile', 'tmobile'],
  'VZ':    ['verizon'],
  'T':     ['at&t', 'att'],
  'CMCSA': ['comcast', 'xfinity', 'nbc'],
  'DIS':   ['disney', 'marvel', 'pixar'],
  'NFLX':  ['netflix'],
  'LIN':   ['linde'],
  'GLW':   ['corning'],
  'ACN':   ['accenture'],
  'NXPI':  ['nxp'],
  'ADI':   ['analog devices'],
  'AMAT':  ['applied materials'],
  'LRCX':  ['lam research'],
  'KLAC':  ['kla'],
  'MRVL':  ['marvell'],
  'MU':    ['micron'],
  'WDC':   ['western digital'],
  'SNDK':  ['sandisk'],
  'GEV':   ['ge vernova'],
  'APP':   ['applovin'],
  'VRT':   ['vertiv'],
  'PLD':   ['prologis'],
  'WELL':  ['welltower'],
  'CB':    ['chubb'],
  'APH':   ['amphenol'],
  'PH':    ['parker hannifin'],
};

// ── 狀態
let companies = [];
let activeSector = 'all';
let activeIndex  = 'all';   // 'all' | 'sp500' | 'nasdaq100'
let sortBy       = 'weight'; // 'weight' | 'ticker' | 'name'
let searchQuery  = '';

// ── 工具函數
function tickerToFile(ticker) {
  return ticker.replace(/[./]/g, '-').toUpperCase();
}

function sectorClass(sector) {
  return 'sector-' + sector.replace(/\s+/g, '-');
}

/**
 * 智慧搜尋：比對 ticker、公司名稱、別名、行業（英中）
 */
function matchSearch(c, query) {
  if (!query) return true;
  const q = query.toLowerCase().trim();
  if (!q) return true;

  // 直接比對 ticker（支援 BRK.B → BRK-B）
  const normalizedTicker = c.ticker.toLowerCase().replace(/-/g, '.');
  if (c.ticker.toLowerCase().includes(q)) return true;
  if (normalizedTicker.includes(q)) return true;

  // 公司名稱
  if (c.name.toLowerCase().includes(q)) return true;

  // 行業（英文 + 中文）
  if (c.sector.toLowerCase().includes(q)) return true;
  const zhSector = (SECTOR_ZH[c.sector] || '').toLowerCase();
  if (zhSector.includes(q)) return true;

  // 別名
  const aliases = SEARCH_ALIASES[c.ticker] || [];
  if (aliases.some(a => a.includes(q) || q.includes(a))) return true;

  return false;
}

// ── 排序函數
function sortCompanies(arr) {
  return [...arr].sort((a, b) => {
    if (sortBy === 'weight') return b.weight - a.weight;
    if (sortBy === 'ticker') return a.ticker.localeCompare(b.ticker);
    if (sortBy === 'name')   return a.name.localeCompare(b.name);
    return 0;
  });
}

// ── 渲染單張卡片
function renderCard(c) {
  const file = tickerToFile(c.ticker);
  const topSegs = c.revenue_segments.slice(0, 4);
  const sectorZh = SECTOR_ZH[c.sector] || c.sector;

  const segsHtml = topSegs.map(s => `
    <div class="seg-row">
      <span class="seg-label">${s.segment}</span>
      <div class="seg-bar-wrap"><div class="seg-bar" style="width:${s.percentage}%"></div></div>
      <span class="seg-pct">${s.percentage}%</span>
    </div>`).join('');

  const ndxBadge = c.nasdaq100
    ? `<span class="index-badge index-badge-ndx"><span class="idx-dot"></span>Nasdaq 100</span>`
    : '';
  const indexStrip = `
    <div class="index-strip">
      <span class="index-badge index-badge-sp"><span class="idx-dot"></span>S&amp;P 500</span>
      ${ndxBadge}
    </div>`;

  const lastUpdated = c.last_updated || 'N/A';

  return `
    <a class="card" href="stocks/${file}.html">
      <div class="card-header">
        <div class="ticker-badge">${c.ticker}</div>
        <div class="weight-badge">SPY ${c.weight.toFixed(2)}%</div>
      </div>
      <div class="company-name">${c.name}</div>
      <div class="badge-row">
        <span class="sector-tag ${sectorClass(c.sector)}">${c.sector} <span style="opacity:.7">${sectorZh}</span></span>
      </div>
      ${indexStrip}
      <div class="description">${c.description}</div>
      <div class="segments">${segsHtml}</div>
      <div class="card-footer">
        <span class="view-link">查看詳情 →</span>
        <span class="updated-info">更新：${lastUpdated}</span>
      </div>
    </a>`;
}

// ── 渲染整個 Grid
function renderGrid() {
  const grid = document.getElementById('grid');
  let filtered = companies;

  // 指數篩選
  if (activeIndex === 'nasdaq100') {
    filtered = filtered.filter(c => c.nasdaq100);
  }
  // S&P 500 = 全部（所有企業均為 S&P 500 成分股）

  // 行業篩選
  if (activeSector !== 'all') {
    filtered = filtered.filter(c => c.sector === activeSector);
  }

  // 搜尋
  if (searchQuery) {
    filtered = filtered.filter(c => matchSearch(c, searchQuery));
  }

  // 排序
  filtered = sortCompanies(filtered);

  // 更新結果計數
  const resultCount = document.getElementById('result-count');
  if (resultCount) {
    resultCount.textContent = `顯示 ${filtered.length} / ${companies.length} 間企業`;
  }

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div class="no-results">
        <div class="icon">🔍</div>
        <p>找不到符合條件的企業</p>
        <p style="font-size:12px;margin-top:8px;opacity:.6">試試搜尋公司別名，例如「Google」可找到 GOOGL</p>
      </div>`;
  } else {
    grid.innerHTML = filtered.map(renderCard).join('');
  }
}

// ── 建立行業篩選按鈕
function buildSectorFilters(data) {
  const sectors = [...new Set(data.map(c => c.sector))].sort();
  const filterGroup = document.getElementById('sector-filters');

  sectors.forEach(s => {
    const zh = SECTOR_ZH[s] || '';
    const btn = document.createElement('button');
    btn.className = 'filter-btn';
    btn.dataset.sector = s;
    btn.innerHTML = `${s} <span class="zh">${zh}</span>`;
    btn.addEventListener('click', () => {
      activeSector = s;
      document.querySelectorAll('#sector-filters .filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderGrid();
    });
    filterGroup.appendChild(btn);
  });
}

// ── 初始化事件監聽
function initEvents() {
  // 搜尋框
  document.getElementById('search').addEventListener('input', e => {
    searchQuery = e.target.value;
    renderGrid();
  });

  // 行業篩選（靜態按鈕：全部）
  document.getElementById('sector-filters').addEventListener('click', e => {
    const btn = e.target.closest('.filter-btn');
    if (!btn) return;
    const sector = btn.dataset.sector;
    if (!sector) return;
    activeSector = sector;
    document.querySelectorAll('#sector-filters .filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderGrid();
  });

  // 指數 Toggle（S&P 500 / Nasdaq 100 / 全部）
  document.getElementById('index-toggles').addEventListener('click', e => {
    const btn = e.target.closest('.toggle-btn');
    if (!btn) return;
    activeIndex = btn.dataset.index;
    document.querySelectorAll('#index-toggles .toggle-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderGrid();
  });

  // 排序
  document.getElementById('sort-select').addEventListener('change', e => {
    sortBy = e.target.value;
    renderGrid();
  });
}

// ── 主程式入口
document.addEventListener('DOMContentLoaded', () => {
  initEvents();

  fetch('data/processed/companies.json')
    .then(r => r.json())
    .then(data => {
      companies = data;

      // 更新統計數字
      const nasdaqCount = data.filter(c => c.nasdaq100).length;
      document.getElementById('total-count').textContent = data.length;
      document.getElementById('nasdaq-count').textContent = nasdaqCount;

      // 建立行業篩選按鈕
      buildSectorFilters(data);

      // 初始渲染
      renderGrid();
    })
    .catch(err => {
      console.error('Failed to load companies.json:', err);
      document.getElementById('grid').innerHTML =
        `<div class="no-results"><div class="icon">⚠️</div><p>資料載入失敗，請稍後重試。</p></div>`;
    });
});
