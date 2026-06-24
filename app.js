/**
 * app.js — US Stock Insight 主頁互動邏輯
 * ==========================================
 * 功能：
 *  - 從 companies.json 動態載入企業資料
 *  - 行業篩選（英文 + 中文雙語）
 *  - 指數篩選 toggle（全部 / S&P 500 / Nasdaq 100）
 *  - 排序（SPY 權重 / Ticker 代號 / 公司名稱）
 *    - 非 S&P 500 企業（in_sp500=false）按權重排序時固定排在最後
 *  - 智慧搜尋（支援 Ticker、公司名稱、中文別名、行業）
 *  - Reset Filter 按鈕（一鍵清除所有篩選條件）
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
  'XOM':   ['exxon', 'mobil', 'exxonmobil'],
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
  'NEE':   ['nextera'],
  'BLK':   ['blackrock'],
  'BX':    ['blackstone'],
  'SCHW':  ['schwab', 'charles schwab'],
  'AXP':   ['american express', 'amex'],
  'COF':   ['capital one'],
  'PGR':   ['progressive'],
  'SPGI':  ['s&p global', 'sp global'],
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
  // 非 S&P 500 企業別名
  'TSM':   ['台積電', 'tsmc', 'taiwan semiconductor', '台灣積體電路'],
  'UMAC':  ['unusual machines', 'drone', '無人機'],
  'FUTU':  ['富途', 'futu', 'moomoo', '富途牛牛', 'futubull'],
};

// ── 狀態
let companies   = [];
let activeSector = 'all';
let activeIndex  = 'all';    // 'all' | 'sp500' | 'nasdaq100'
let sortBy       = 'weight'; // 'weight' | 'ticker' | 'name'
let searchQuery  = '';

// ── 工具函數
function tickerToFile(ticker) {
  return ticker.replace(/[./]/g, '-').toUpperCase();
}

function sectorClass(sector) {
  return 'sector-' + sector.replace(/\s+/g, '-');
}

/** 判斷篩選條件是否全部為預設值 */
function isDefaultState() {
  return activeSector === 'all' &&
         activeIndex  === 'all' &&
         sortBy       === 'weight' &&
         searchQuery  === '';
}

/** 更新 reset 按鈕的顯示狀態 */
function updateResetBtn() {
  const btn = document.getElementById('reset-btn');
  if (!btn) return;
  // 使用 visibility + opacity 而非 display，避免 CSS specificity 問題
  if (isDefaultState()) {
    btn.style.visibility = 'hidden';
    btn.style.opacity = '0';
    btn.style.pointerEvents = 'none';
  } else {
    btn.style.visibility = 'visible';
    btn.style.opacity = '1';
    btn.style.pointerEvents = 'auto';
  }
}

/**
 * 智慧搜尋：比對 ticker、公司名稱、別名、行業（英中）
 *
 * 匹配規則：
 *  - Ticker：完整包含比對（大小寫不敏感）
 *  - 公司名稱：需要字詞首字匹配（word-boundary），避免 "mac" 匹配 "Comcast"
 *  - 行業：完整行業名稱包含比對（英文）或完全相等（中文）
 *  - 別名：單向比對（alias.includes(q)），要求 q 至少 2 字元，避免短別名過度匹配
 */
function matchSearch(c, query) {
  if (!query) return true;
  const q = query.toLowerCase().trim();
  if (!q) return true;

  // 1. Ticker 完整包含比對（支援 BRK.B → BRK-B）
  if (c.ticker.toLowerCase().includes(q)) return true;
  if (c.ticker.toLowerCase().replace(/-/g, '.').includes(q)) return true;

  // 2. 公司名稱：要求字詞首字匹配（word-boundary）
  //    例："apple" 匹配 "Apple Inc." 但不匹配 "Snapple"
  const nameLower = c.name.toLowerCase();
  if (nameLower === q) return true; // 完全相等
  // 字詞首字匹配：字詞開頭或空白/連字符後緊接跟著查詢字串
  const wordBoundaryRe = new RegExp('(?:^|[\\s\\-\/])' + q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  if (wordBoundaryRe.test(nameLower)) return true;

  // 3. 行業：英文完整包含（避免 substring 誤匹）或中文完全相等
  if (c.sector.toLowerCase().includes(q)) return true;
  const zhSector = (SECTOR_ZH[c.sector] || '').toLowerCase();
  if (zhSector === q || zhSector.startsWith(q)) return true;

  // 4. 別名：單向比對（alias.includes(q)），要求 q 至少 2 字元
  //    避免短別名（amd、nbc、fb、mac）對長字串的過度匹配
  if (q.length >= 2) {
    const aliases = SEARCH_ALIASES[c.ticker] || [];
    if (aliases.some(a => a.toLowerCase().includes(q))) return true;
  }

  return false;
}

/**
 * 排序函數
 * 規則：非 S&P 500 企業（in_sp500=false）所有排序方式均固定排在最後。
 *       QQQ weight 排序時，非 Nasdaq 100 成員排在 Nasdaq 100 成員之後。
 */
function sortCompanies(arr) {
  return [...arr].sort((a, b) => {
    const aInSP = a.in_sp500 !== false;
    const bInSP = b.in_sp500 !== false;

    // 非 S&P 500 企業永遠排在最後（所有排序方式均適用）
    if (aInSP !== bInSP) return aInSP ? -1 : 1;

    // 同組內的排序邏輯
    if (sortBy === 'weight') {
      if (aInSP) return b.weight - a.weight;
      return a.ticker.localeCompare(b.ticker);
    }
    if (sortBy === 'ticker') return a.ticker.localeCompare(b.ticker);
    if (sortBy === 'name')   return a.name.localeCompare(b.name);
    if (sortBy === 'qqq_weight') {
      // QQQ weight 排序：先將 Nasdaq 100 成員排在前面，再按 qqq_weight 降冪
      const aQQQ = a.qqq_weight || 0;
      const bQQQ = b.qqq_weight || 0;
      const aInNDX = aQQQ > 0;
      const bInNDX = bQQQ > 0;
      // Nasdaq 100 成員排在非成員之前
      if (aInNDX !== bInNDX) return aInNDX ? -1 : 1;
      // 同組內按 qqq_weight 降冪（非成員組內按 SPY weight 降冪）
      if (aInNDX) return bQQQ - aQQQ;
      return b.weight - a.weight;
    }
    return 0;
  });
}

/**
 * HTML 變數轉義：將字串中的特殊字元轉為 HTML 實體
 * 防止 XSS 與版面崩潰，所有來自 JSON 的動態內容必須經此函數處理
 */
function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ── 渲染單張卡片
function renderCard(c) {
  const file = tickerToFile(c.ticker);
  // 業務板塊已在 companies.json 中按百分比降床排序，取前 4 項
  const topSegs = c.revenue_segments.slice(0, 4);
  const sectorZh = SECTOR_ZH[c.sector] || c.sector;

  const segsHtml = topSegs.map(s => `
    <div class="seg-row">
      <span class="seg-label">${escapeHtml(s.segment)}</span>
      <div class="seg-bar-wrap"><div class="seg-bar" style="width:${Number(s.percentage)}%"></div></div>
      <span class="seg-pct">${Number(s.percentage)}%</span>
    </div>`).join('');

  // 指數 badges
  const spBadge = c.in_sp500 !== false
    ? `<span class="index-badge index-badge-sp"><span class="idx-dot"></span>S&amp;P 500</span>`
    : '';
  const ndxBadge = c.nasdaq100
    ? `<span class="index-badge index-badge-ndx"><span class="idx-dot"></span>Nasdaq 100</span>`
    : '';
  // 非 S&P 500 企業顯示「自選」 badge
  const watchBadge = c.in_sp500 === false
    ? `<span class="index-badge index-badge-watch"><span class="idx-dot"></span>自選</span>`
    : '';

  const indexStrip = `<div class="index-strip">${spBadge}${ndxBadge}${watchBadge}</div>`;

  // 權重顯示：依目前排序方式動態顯示 SPY 或 QQQ 權重
  let weightHtml;
  if (c.in_sp500 === false) {
    weightHtml = `<div class="weight-badge weight-badge-watch">自選追蹤</div>`;
  } else if (sortBy === 'qqq_weight' && c.qqq_weight > 0) {
    weightHtml = `<div class="weight-badge weight-badge-qqq">QQQ ${c.qqq_weight.toFixed(2)}%</div>`;
  } else {
    weightHtml = `<div class="weight-badge">SPY ${c.weight.toFixed(2)}%</div>`;
  }

  const lastUpdated = escapeHtml(c.last_updated || 'N/A');

  return `
    <a class="card" href="stocks/${file}.html">
      <div class="card-header">
        <div class="ticker-badge">${escapeHtml(c.ticker)}</div>
        ${weightHtml}
      </div>
      <div class="company-name">${escapeHtml(c.name)}</div>
      <div class="badge-row">
        <span class="sector-tag ${sectorClass(c.sector)}">${escapeHtml(c.sector)} <span style="opacity:.7">${escapeHtml(sectorZh)}</span></span>
      </div>
      ${indexStrip}
      <div class="description">${escapeHtml(c.description)}</div>
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
  } else if (activeIndex === 'sp500') {
    filtered = filtered.filter(c => c.in_sp500 !== false);
  }

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

  // 更新 reset 按鈕顯示
  updateResetBtn();

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div class="no-results">
        <div class="icon">🔍</div>
        <p>找不到符合條件的企業</p>
        <p style="font-size:12px;margin-top:8px;opacity:.6">試試搜尋公司別名，例如「Google」可找到 GOOGL，「台積電」可找到 TSM</p>
      </div>`;
  } else {
    grid.innerHTML = filtered.map(renderCard).join('');
  }
}

// ── 重置所有篩選條件
function resetFilters() {
  activeSector = 'all';
  activeIndex  = 'all';
  sortBy       = 'weight';
  searchQuery  = '';

  // 重置 UI 狀態
  document.getElementById('search').value = '';
  document.getElementById('sort-select').value = 'weight';

  document.querySelectorAll('#sector-filters .filter-btn').forEach(b => b.classList.remove('active'));
  const allSectorBtn = document.querySelector('#sector-filters .filter-btn[data-sector="all"]');
  if (allSectorBtn) allSectorBtn.classList.add('active');

  document.querySelectorAll('#index-toggles .toggle-btn').forEach(b => b.classList.remove('active'));
  const allIndexBtn = document.querySelector('#index-toggles .toggle-btn[data-index="all"]');
  if (allIndexBtn) allIndexBtn.classList.add('active');

  renderGrid();
}

// ── 建立行業篩選按鈕—僅建立 DOM，不綁定個別 click handler
// 事件處理全部由 initEvents 中的事件委派（event delegation）負責
function buildSectorFilters(data) {
  const sectors = [...new Set(data.map(c => c.sector))].sort();
  const filterGroup = document.getElementById('sector-filters');

  sectors.forEach(s => {
    const zh = SECTOR_ZH[s] || '';
    const btn = document.createElement('button');
    btn.className = 'filter-btn';
    btn.dataset.sector = s;
    btn.innerHTML = `${s} <span class="zh">${zh}</span>`;
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

  // 行業篩選（支援 toggle：再次點擊已選中的行業可取消篩選）
  document.getElementById('sector-filters').addEventListener('click', e => {
    const btn = e.target.closest('.filter-btn');
    if (!btn) return;
    const sector = btn.dataset.sector;
    if (!sector) return;
    // 若點擊的是已選中的非「全部」按鈕，則取消篩選（回到全部）
    if (activeSector === sector && sector !== 'all') {
      activeSector = 'all';
      document.querySelectorAll('#sector-filters .filter-btn').forEach(b => b.classList.remove('active'));
      const allBtn = document.querySelector('#sector-filters .filter-btn[data-sector="all"]');
      if (allBtn) allBtn.classList.add('active');
    } else {
      activeSector = sector;
      document.querySelectorAll('#sector-filters .filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    }
    renderGrid();
  });

  // 指數 Toggle（支援 toggle：再次點擊已選中的指數可取消篩選）
  document.getElementById('index-toggles').addEventListener('click', e => {
    const btn = e.target.closest('.toggle-btn');
    if (!btn) return;
    const idx = btn.dataset.index;
    // 若點擊的是已選中的非「全部」按鈕，則取消篩選（回到全部）
    if (activeIndex === idx && idx !== 'all') {
      activeIndex = 'all';
      document.querySelectorAll('#index-toggles .toggle-btn').forEach(b => b.classList.remove('active'));
      const allBtn = document.querySelector('#index-toggles .toggle-btn[data-index="all"]');
      if (allBtn) allBtn.classList.add('active');
    } else {
      activeIndex = idx;
      document.querySelectorAll('#index-toggles .toggle-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    }
    renderGrid();
  });

  // 排序
  document.getElementById('sort-select').addEventListener('change', e => {
    sortBy = e.target.value;
    renderGrid();
  });

  // Reset Filter 按鈕
  const resetBtn = document.getElementById('reset-btn');
  if (resetBtn) {
    resetBtn.addEventListener('click', resetFilters);
  }
}

// ── 主程式入口
document.addEventListener('DOMContentLoaded', () => {
  initEvents();

  // 加入 cache-busting 參數，確保每次載入最新資料
  const cacheBuster = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  fetch(`data/processed/companies.json?v=${cacheBuster}`)
    .then(r => r.json())
    .then(data => {
      companies = data;

      // 更新統計數字
      const sp500Count   = data.filter(c => c.in_sp500 !== false).length;
      const nasdaqCount  = data.filter(c => c.nasdaq100).length;
      document.getElementById('total-count').textContent  = data.length;
      document.getElementById('sp500-count').textContent  = sp500Count;
      document.getElementById('nasdaq-count').textContent = nasdaqCount;

      // 建立行業篩選按鈕
      buildSectorFilters(data);

      // 初始渲染（reset 按鈕預設隱藏）
      updateResetBtn();
      renderGrid();
    })
    .catch(err => {
      console.error('Failed to load companies.json:', err);
      document.getElementById('grid').innerHTML =
        `<div class="no-results"><div class="icon">⚠️</div><p>資料載入失敗，請稍後重試。</p></div>`;
    });
});
