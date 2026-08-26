// ── ledger.js ─────────────────────────────────────────────────────────────
let _ledgerState = { page: 1, total: 0, pages: 0, filters: {}, sortBy: 'date', sortDir: 'desc' };
let _categories = [];
let _members = [];
let _banks = [];

async function renderLedger() {
  const root = document.getElementById('page-root');
  root.innerHTML = `
    <div class="page-header fade-in">
      <h2>📋 Transaction Ledger</h2>
      <p>Full transaction history with filtering, search, and inline category editing</p>
    </div>
    <div class="page-content fade-in">
      <div class="card" style="margin-bottom:20px">
        <div class="filter-bar">
          <input class="search" type="text" id="f-search" placeholder="🔍 Search merchant..." />
          <select id="f-type"><option value="">All Types</option><option value="Debit">Debit</option><option value="Credit">Credit</option></select>
          <select id="f-cat"><option value="">All Categories</option></select>
          <select id="f-member"><option value="">All Members</option></select>
          <select id="f-bank"><option value="">All Banks</option></select>
          <input type="date" id="f-start" title="Start date" />
          <input type="date" id="f-end" title="End date" />
          <button class="btn btn-primary btn-sm" onclick="applyLedgerFilters()">Apply</button>
          <button class="btn btn-secondary btn-sm" onclick="clearLedgerFilters()">Clear</button>
        </div>
        <div class="filter-bar" style="margin-top:10px; padding-top:10px; border-top:1px solid var(--border); justify-content:flex-end;">
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
            <span style="font-size:.72rem;color:var(--text-3);text-transform:uppercase;letter-spacing:.08em;font-weight:700;">Sort</span>
            <select id="f-sort-by" title="Sort by">
              <option value="date">Date</option>
              <option value="merchant">Merchant</option>
              <option value="amount">Amount</option>
              <option value="type">Type</option>
              <option value="category">Category</option>
              <option value="member">Household Member</option>
              <option value="bank">Bank</option>
            </select>
            <select id="f-sort-dir" title="Sort direction">
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
            <button class="btn btn-primary btn-sm" onclick="applyLedgerSort()">Apply</button>
            <button class="btn btn-secondary btn-sm" onclick="resetLedgerSort()">Reset</button>
          </div>
        </div>
        <div id="ledger-count" style="font-size:.8rem;color:var(--text-3);margin-bottom:8px;"></div>
        <div class="table-wrap" id="ledger-table">
          <div class="skeleton" style="height:300px;border-radius:8px;"></div>
        </div>
        <div class="pagination" id="ledger-pagination"></div>
      </div>
    </div>`;

  // Load categories, members, and banks for dropdowns
  try {
    const [cats, mems, banks] = await Promise.all([
      API.get('/api/rules/categories'),
      API.get('/api/members'),
      API.get('/api/members/banks')
    ]);
    _categories = cats;
    _members = mems;
    _banks = banks;

    const catSel = document.getElementById('f-cat');
    _categories.forEach(c => {
      const o = document.createElement('option');
      o.value = c.category_id; o.textContent = `${c.icon} ${c.category_name}`;
      catSel.appendChild(o);
    });

    const memSel = document.getElementById('f-member');
    _members.forEach(m => {
      const o = document.createElement('option');
      o.value = m.member_id; o.textContent = `👤 ${m.member_name}`;
      memSel.appendChild(o);
    });

    const bankSel = document.getElementById('f-bank');
    _banks.forEach(b => {
      const o = document.createElement('option');
      o.value = b.bank_id; o.textContent = `${b.icon || '🏛️'} ${b.bank_name}`;
      bankSel.appendChild(o);
    });
  } catch {}

  // Search on Enter
  document.getElementById('f-search').addEventListener('keydown', e => {
    if (e.key === 'Enter') applyLedgerFilters();
  });

  const sortBy = document.getElementById('f-sort-by');
  const sortDir = document.getElementById('f-sort-dir');
  if (sortBy) sortBy.value = _ledgerState.sortBy || 'date';
  if (sortDir) sortDir.value = _ledgerState.sortDir || 'desc';

  _ledgerState = { page: 1, filters: {}, sortBy: 'date', sortDir: 'desc' };
  await fetchLedger();
}

async function fetchLedger() {
  const state = _ledgerState;
  const params = new URLSearchParams({
    page: state.page,
    page_size: 50,
    sort_by: state.sortBy || 'date',
    sort_dir: state.sortDir || 'desc',
    ...state.filters
  });
  try {
    const data = await API.get(`/api/transactions?${params}`);
    state.total = data.total;
    state.pages = data.pages;
    renderLedgerTable(data.transactions);
    renderPagination();
    document.getElementById('ledger-count').textContent =
      `Showing ${data.transactions.length} of ${data.total} transactions`;
  } catch (e) {
    toast('Failed to load transactions: ' + e.message, 'error');
  }
}

function applyLedgerFilters() {
  const f = {};
  const search = document.getElementById('f-search').value.trim();
  const type = document.getElementById('f-type').value;
  const cat = document.getElementById('f-cat').value;
  const member = document.getElementById('f-member').value;
  const bank = document.getElementById('f-bank').value;
  const start = document.getElementById('f-start').value;
  const end = document.getElementById('f-end').value;

  if (search) f.search_text = search;
  if (type) f.transaction_type = type;
  if (cat) f.category_id = cat;
  if (member) f.member_id = member;
  if (bank) f.bank_id = bank;
  if (start) f.start_date = start;
  if (end) f.end_date = end;

  _ledgerState.filters = f;
  _ledgerState.page = 1;
  fetchLedger();
}

function applyLedgerSort() {
  const sortBy = document.getElementById('f-sort-by')?.value || 'date';
  const sortDir = document.getElementById('f-sort-dir')?.value || 'desc';

  _ledgerState.sortBy = sortBy;
  _ledgerState.sortDir = sortDir;
  _ledgerState.page = 1;
  fetchLedger();
}

function resetLedgerSort() {
  const sortBy = document.getElementById('f-sort-by');
  const sortDir = document.getElementById('f-sort-dir');
  if (sortBy) sortBy.value = 'date';
  if (sortDir) sortDir.value = 'desc';

  _ledgerState.sortBy = 'date';
  _ledgerState.sortDir = 'desc';
  _ledgerState.page = 1;
  fetchLedger();
}

function clearLedgerFilters() {
  ['f-search','f-start','f-end'].forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
  ['f-type','f-cat','f-member','f-bank'].forEach(id => { const el = document.getElementById(id); if (el) el.selectedIndex = 0; });
  const sortBy = document.getElementById('f-sort-by');
  const sortDir = document.getElementById('f-sort-dir');
  if (sortBy) sortBy.value = 'date';
  if (sortDir) sortDir.value = 'desc';

  _ledgerState.filters = {};
  _ledgerState.sortBy = 'date';
  _ledgerState.sortDir = 'desc';
  _ledgerState.page = 1;
  fetchLedger();
}

function renderLedgerTable(txs) {
  const el = document.getElementById('ledger-table');
  if (!el) return;
  if (!txs.length) {
    el.innerHTML = `<div class="empty-state"><div class="empty-icon">📭</div><h3>No transactions found</h3><p>Try adjusting your filters or uploading a statement</p></div>`;
    return;
  }
  const catOptions = _categories.map(c => `<option value="${c.category_id}">${c.icon} ${c.category_name}</option>`).join('');
  const memOptions = _members.map(m => `<option value="${m.member_id}">👤 ${escapeHtml(m.member_name)}</option>`).join('');

  el.innerHTML = `<table>
    <thead><tr><th>Date</th><th>Merchant</th><th>Amount</th><th>Type</th><th>Category</th><th>Bank</th><th>Household Member</th></tr></thead>
    <tbody>${txs.map(t => `
      <tr>
        <td style="font-size:.8rem;color:var(--text-3);font-family:var(--mono)">${t.transaction_date}</td>
        <td><div style="font-weight:500;color:var(--text-1)">${escapeHtml(t.clean_merchant)}</div><div style="font-size:.72rem;color:var(--text-3)">${escapeHtml(t.merchant_description?.slice(0,45) || '')}</div></td>
        <td class="${t.transaction_type==='Debit'?'amount-debit':'amount-credit'}">${t.transaction_type==='Debit'?'−':'+'}${t.amount_fmt}</td>
        <td><span class="badge ${t.transaction_type==='Debit'?'badge-rose':'badge-green'}">${t.transaction_type}</span></td>
        <td>
          <select class="cat-select" data-id="${t.transaction_id}" style="background:transparent;border:1px solid var(--border);color:var(--text-2);border-radius:6px;padding:3px 6px;font-size:.78rem;cursor:pointer;outline:none">
            ${catOptions}
          </select>
        </td>
        <td style="font-size:.82rem;color:var(--text-2)">${escapeHtml(t.bank_name)}</td>
        <td>
          <span style="display:inline-flex;align-items:center;gap:6px;padding:4px 8px;border-radius:999px;background:rgba(255,255,255,0.03);border:1px solid var(--border);color:var(--text-2);font-size:.78rem;">
            👤 ${escapeHtml(t.member_name || 'Unassigned')}
          </span>
        </td>
      </tr>`).join('')}</tbody></table>`;

  // Set current category & member values and attach change listeners
  el.querySelectorAll('.cat-select').forEach(sel => {
    const tx = txs.find(t => t.transaction_id === sel.dataset.id);
    if (tx) sel.value = tx.category_id;
    sel.addEventListener('change', async () => {
      try {
        await API.patch(`/api/transactions/${sel.dataset.id}/category`, { category_id: +sel.value });
        toast('Category updated', 'success');
      } catch (e) { toast(e.message, 'error'); }
    });
  });

}

function renderPagination() {
  const el = document.getElementById('ledger-pagination');
  if (!el || _ledgerState.pages <= 1) { if (el) el.innerHTML = ''; return; }
  const { page, pages } = _ledgerState;
  let html = `<button class="page-btn" ${page<=1?'disabled':''} onclick="goLedgerPage(${page-1})">‹</button>`;
  for (let i = Math.max(1, page-2); i <= Math.min(pages, page+2); i++) {
    html += `<button class="page-btn ${i===page?'active':''}" onclick="goLedgerPage(${i})">${i}</button>`;
  }
  html += `<button class="page-btn ${page>=pages?'disabled':''} onclick="goLedgerPage(${page+1})">›</button>`;
  el.innerHTML = html;
}

function goLedgerPage(p) {
  _ledgerState.page = p;
  fetchLedger();
}
