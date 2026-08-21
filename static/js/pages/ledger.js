// ── ledger.js ─────────────────────────────────────────────────────────────
let _ledgerState = { page: 1, total: 0, pages: 0, filters: {} };
let _categories = [];
let _members = [];

async function renderLedger() {
  const root = document.getElementById('page-root');
  root.innerHTML = `
    <div class="page-header fade-in">
      <h2>📋 Transaction Ledger</h2>
      <p>Full transaction history with filtering, search, and inline category & member editing</p>
    </div>
    <div class="page-content fade-in">
      <div class="card" style="margin-bottom:20px">
        <div class="filter-bar">
          <input class="search" type="text" id="f-search" placeholder="🔍 Search merchant..." />
          <select id="f-type"><option value="">All Types</option><option value="Debit">Debit</option><option value="Credit">Credit</option></select>
          <select id="f-cat"><option value="">All Categories</option></select>
          <select id="f-member"><option value="">All Members</option></select>
          <input type="date" id="f-start" title="Start date" />
          <input type="date" id="f-end" title="End date" />
          <button class="btn btn-primary btn-sm" onclick="applyLedgerFilters()">Apply</button>
          <button class="btn btn-secondary btn-sm" onclick="clearLedgerFilters()">Clear</button>
        </div>
        <div id="ledger-count" style="font-size:.8rem;color:var(--text-3);margin-bottom:8px;"></div>
        <div class="table-wrap" id="ledger-table">
          <div class="skeleton" style="height:300px;border-radius:8px;"></div>
        </div>
        <div class="pagination" id="ledger-pagination"></div>
      </div>
    </div>`;

  // Load categories and members for dropdowns
  try {
    const [cats, mems] = await Promise.all([
      API.get('/api/rules/categories'),
      API.get('/api/members')
    ]);
    _categories = cats;
    _members = mems;

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
  } catch {}

  // Search on Enter
  document.getElementById('f-search').addEventListener('keydown', e => {
    if (e.key === 'Enter') applyLedgerFilters();
  });

  _ledgerState = { page: 1, filters: {} };
  await fetchLedger();
}

async function fetchLedger() {
  const state = _ledgerState;
  const params = new URLSearchParams({ page: state.page, page_size: 50, ...state.filters });
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
  const start = document.getElementById('f-start').value;
  const end = document.getElementById('f-end').value;
  if (search) f.search_text = search;
  if (type) f.transaction_type = type;
  if (cat) f.category_id = cat;
  if (member) f.member_id = member;
  if (start) f.start_date = start;
  if (end) f.end_date = end;
  _ledgerState.filters = f;
  _ledgerState.page = 1;
  fetchLedger();
}

function clearLedgerFilters() {
  ['f-search','f-start','f-end'].forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
  ['f-type','f-cat','f-member'].forEach(id => { const el = document.getElementById(id); if (el) el.selectedIndex = 0; });
  _ledgerState.filters = {};
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
          <select class="member-select" data-id="${t.transaction_id}" style="background:transparent;border:1px solid var(--border);color:var(--text-2);border-radius:6px;padding:3px 6px;font-size:.78rem;cursor:pointer;outline:none">
            ${memOptions}
          </select>
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

  el.querySelectorAll('.member-select').forEach(sel => {
    const tx = txs.find(t => t.transaction_id === sel.dataset.id);
    if (tx && tx.member_id) sel.value = tx.member_id;
    sel.addEventListener('change', async () => {
      try {
        await API.patch(`/api/transactions/${sel.dataset.id}/member`, { member_id: +sel.value });
        toast('Member updated', 'success');
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
