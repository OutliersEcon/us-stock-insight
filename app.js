/**
 * app.js — US Stock Insight 主頁互動邏輯
 * ==========================================
 * 功能：
 *  - 從 companies.json 動態載入企業資料
 *  - 行業篩選（英文 + 中文雙語）
 *  - 指數篩選 toggle（全部 / S&P 500 / Nasdaq 100）
 *  - 排序（SPY 權重 / QQQ 權重 / Ticker 代號 / 公司名稱）
 *    - 非 S&P 500 企業（in_sp500=false）按任何方式排序時固定排在最後
 *  - 智慧搜尋（支援 Ticker、公司名稱、中文別名、行業）
 *  - Reset Filter 按鈕（一鍵清除所有篩選條件）
 *  - Pagination：每頁 25 / 50 / 100 / 全部，上下方均有頁碼導覽列
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
let companies    = [];
let activeSector = 'all';
let activeIndex  = 'all';     // 'all' | 'sp500' | 'nasdaq100'
let sortBy       = 'weight';  // 'weight' | 'qqq_weight' | 'ticker' | 'name'
let searchQuery  = '';
let currentPage  = 1;
let pageSize     = 25;        // 25 | 50 | 100 | 0（0 = 全部）

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
         searchQuery  === '' &&
         pageSize     === 25;
}

/** 更新 reset 按鈕的顯示狀態 */
function updateResetBtn() {
  const btn = document.getElementById('reset-btn');
  if (!btn) return;
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
  const nameLower = c.name.toLowerCase();
  if (nameLower === q) return true;
  const wordBoundaryRe = new RegExp('(?:^|[\\s\\-\/])' + q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  if (wordBoundaryRe.test(nameLower)) return true;

  // 3. 行業：英文完整包含或中文完全相等
  if (c.sector.toLowerCase().includes(q)) return true;
  const zhSector = (SECTOR_ZH[c.sector] || '').toLowerCase();
  if (zhSector === q || zhSector.startsWith(q)) return true;

  // 4. 別名：單向比對（alias.includes(q)），要求 q 至少 2 字元
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
      const aQQQ = a.qqq_weight || 0;
      const bQQQ = b.qqq_weight || 0;
      const aInNDX = aQQQ > 0;
      const bInNDX = bQQQ > 0;
      if (aInNDX !== bInNDX) return aInNDX ? -1 : 1;
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

/**
 * 渲染 Pagination 導覽列（上方或下方均使用此函數）
 * @param {number} totalItems  - 篩選後的總企業數
 * @param {string} position    - 'top' 或 'bottom'，對應 DOM id
 */
function renderPagination(totalItems, position) {
  const container = document.getElementById(`pagination-${position}`);
  if (!container) return;

  // pageSize = 0 表示「全部」，不需要分頁
  if (pageSize === 0 || totalItems === 0) {
    container.innerHTML = '';
    return;
  }

  const totalPages = Math.ceil(totalItems / pageSize);

  // 只有一頁時仍顯示導覽列（讓用戶知道目前狀態）
  let html = `<div class="pagination">`;

  // ← 上一頁
  html += `<button class="page-btn page-prev" ${currentPage === 1 ? 'disabled' : ''} data-page="${currentPage - 1}">‹</button>`;

  // 頁碼按鈕（最多顯示 7 個，超過時用省略號）
  const pages = getPageRange(currentPage, totalPages);
  pages.forEach(p => {
    if (p === '...') {
      html += `<span class="page-ellipsis">…</span>`;
    } else {
      html += `<button class="page-btn ${p === currentPage ? 'active' : ''}" data-page="${p}">${p}</button>`;
    }
  });

  // → 下一頁
  html += `<button class="page-btn page-next" ${currentPage === totalPages ? 'disabled' : ''} data-page="${currentPage + 1}">›</button>`;

  // 頁面資訊
  const start = (currentPage - 1) * pageSize + 1;
  const end   = Math.min(currentPage * pageSize, totalItems);
  html += `<span class="page-info">${start}–${end} / ${totalItems}</span>`;

  html += `</div>`;
  container.innerHTML = html;

  // 綁定點擊事件
  container.querySelectorAll('.page-btn:not([disabled])').forEach(btn => {
    btn.addEventListener('click', () => {
      const p = parseInt(btn.dataset.page);
      if (!isNaN(p) && p !== currentPage) {
        currentPage = p;
        renderGrid();
        // 點擊下方分頁時，捲動到 grid 頂部
        if (position === 'bottom') {
          document.getElementById('grid').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
    });
  });
}

/**
 * 計算要顯示的頁碼範圍（最多 7 個按鈕，超過時加省略號）
 */
function getPageRange(current, total) {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }
  const pages = [];
  if (current <= 4) {
    // 靠近開頭：1 2 3 4 5 … last
    for (let i = 1; i <= 5; i++) pages.push(i);
    pages.push('...');
    pages.push(total);
  } else if (current >= total - 3) {
    // 靠近結尾：1 … (last-4) (last-3) (last-2) (last-1) last
    pages.push(1);
    pages.push('...');
    for (let i = total - 4; i <= total; i++) pages.push(i);
  } else {
    // 中間：1 … (cur-1) cur (cur+1) … last
    pages.push(1);
    pages.push('...');
    pages.push(current - 1);
    pages.push(current);
    pages.push(current + 1);
    pages.push('...');
    pages.push(total);
  }
  return pages;
}

// ── 渲染整個 Grid（含 pagination）
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

  const totalFiltered = filtered.length;

  // 確保 currentPage 不超出範圍
  if (pageSize > 0) {
    const totalPages = Math.ceil(totalFiltered / pageSize);
    if (currentPage > totalPages && totalPages > 0) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;
  }

  // 更新結果計數（含分頁資訊）
  const resultCount = document.getElementById('result-count');
  if (resultCount) {
    if (pageSize === 0 || totalFiltered === 0) {
      resultCount.textContent = `顯示 ${totalFiltered} / ${companies.length} 間企業`;
    } else {
      const totalPages = Math.ceil(totalFiltered / pageSize);
      resultCount.textContent = `顯示 ${totalFiltered} / ${companies.length} 間企業　·　第 ${currentPage} / ${totalPages} 頁`;
    }
  }

  // 更新 reset 按鈕顯示
  updateResetBtn();

  // 分頁切片
  let pageItems = filtered;
  if (pageSize > 0) {
    const start = (currentPage - 1) * pageSize;
    pageItems = filtered.slice(start, start + pageSize);
  }

  // 渲染上方分頁
  renderPagination(totalFiltered, 'top');

  // 渲染卡片
  if (filtered.length === 0) {
    grid.innerHTML = `
      <div class="no-results">
        <div class="icon">🔍</div>
        <p>找不到符合條件的企業</p>
        <p style="font-size:12px;margin-top:8px;opacity:.6">試試搜尋公司別名，例如「Google」可找到 GOOGL，「台積電」可找到 TSM</p>
      </div>`;
  } else {
    grid.innerHTML = pageItems.map(renderCard).join('');
  }

  // 渲染下方分頁
  renderPagination(totalFiltered, 'bottom');
}

// ── 重置所有篩選條件（含分頁）
function resetFilters() {
  activeSector = 'all';
  activeIndex  = 'all';
  sortBy       = 'weight';
  searchQuery  = '';
  currentPage  = 1;
  pageSize     = 25;

  // 重置 UI 狀態
  document.getElementById('search').value = '';
  document.getElementById('sort-select').value = 'weight';

  const pageSizeSelect = document.getElementById('page-size-select');
  if (pageSizeSelect) pageSizeSelect.value = '25';

  document.querySelectorAll('#sector-filters .filter-btn').forEach(b => b.classList.remove('active'));
  const allSectorBtn = document.querySelector('#sector-filters .filter-btn[data-sector="all"]');
  if (allSectorBtn) allSectorBtn.classList.add('active');

  document.querySelectorAll('#index-toggles .toggle-btn').forEach(b => b.classList.remove('active'));
  const allIndexBtn = document.querySelector('#index-toggles .toggle-btn[data-index="all"]');
  if (allIndexBtn) allIndexBtn.classList.add('active');

  renderGrid();
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
    filterGroup.appendChild(btn);
  });
}

// ── 初始化事件監聽
function initEvents() {
  // 搜尋框（搜尋時重置到第一頁）
  document.getElementById('search').addEventListener('input', e => {
    searchQuery = e.target.value;
    currentPage = 1;
    renderGrid();
  });

  // 行業篩選（支援 toggle：再次點擊已選中的行業可取消篩選）
  document.getElementById('sector-filters').addEventListener('click', e => {
    const btn = e.target.closest('.filter-btn');
    if (!btn) return;
    const sector = btn.dataset.sector;
    if (!sector) return;
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
    currentPage = 1;
    renderGrid();
  });

  // 指數 Toggle（支援 toggle：再次點擊已選中的指數可取消篩選）
  document.getElementById('index-toggles').addEventListener('click', e => {
    const btn = e.target.closest('.toggle-btn');
    if (!btn) return;
    const idx = btn.dataset.index;
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
    currentPage = 1;
    renderGrid();
  });

  // 排序（排序改變時重置到第一頁）
  document.getElementById('sort-select').addEventListener('change', e => {
    sortBy = e.target.value;
    currentPage = 1;
    renderGrid();
  });

  // 每頁顯示數量
  document.getElementById('page-size-select').addEventListener('change', e => {
    pageSize = parseInt(e.target.value);
    currentPage = 1;
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

      // 初始渲染
      updateResetBtn();
      renderGrid();
    })
    .catch(err => {
      console.error('Failed to load companies.json:', err);
      document.getElementById('grid').innerHTML =
        `<div class="no-results"><div class="icon">⚠️</div><p>資料載入失敗，請稍後重試。</p></div>`;
    });
});
