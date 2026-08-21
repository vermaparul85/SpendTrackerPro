// ── rules.js ──────────────────────────────────────────────────────────────
async function renderRules() {
  let categories = [];
  try { categories = await API.get('/api/rules/categories'); } catch {}

  const root = document.getElementById('page-root');
  root.innerHTML = `
    <div class="page-header fade-in">
      <h2>🏷️ Rules & Categories</h2>
      <p>Keyword-based auto-categorization rules for transaction classification</p>
    </div>
    <div class="page-content fade-in">
      <div class="grid-2">
        <div class="card">
          <div class="card-title">Add New Rule</div>
          <div class="form-group"><label>Keyword (in merchant description)</label><input type="text" id="r-keyword" placeholder="e.g. SWIGGY, NETFLIX, HPCL"></div>
          <div class="form-group">
            <label>Map to Category</label>
            <select id="r-category">
              ${categories.map(c => `<option value="${c.category_id}">${c.icon} ${c.category_name}</option>`).join('')}
            </select>
          </div>
          <div class="form-group"><label>Clean Merchant Name</label><input type="text" id="r-clean" placeholder="e.g. Swiggy, Netflix, HP Fuel"></div>
          <button class="btn btn-primary btn-full" onclick="submitRule()">+ Add Rule</button>
        </div>
        <div class="card">
          <div class="card-title">Existing Rules</div>
          <div class="table-wrap" id="rules-list">
            <div class="skeleton" style="height:300px;border-radius:8px;"></div>
          </div>
        </div>
      </div>
    </div>`;
  loadRules();
}

async function loadRules() {
  try {
    const rules = await API.get('/api/rules');
    const el = document.getElementById('rules-list');
    if (!el) return;
    if (!rules.length) { el.innerHTML = '<p style="color:var(--text-3);font-size:.85rem;margin-top:8px">No rules yet.</p>'; return; }
    el.innerHTML = `<table>
      <thead><tr><th>Keyword</th><th>Category</th><th>Clean Name</th></tr></thead>
      <tbody>${rules.map(r => `
        <tr>
          <td><code style="font-family:var(--mono);font-size:.8rem;color:var(--blue)">${escapeHtml(r.keyword)}</code></td>
          <td><span class="badge badge-gray">${r.icon||''} ${escapeHtml(r.category_name)}</span></td>
          <td style="font-size:.82rem;color:var(--text-2)">${escapeHtml(r.clean_merchant||'')}</td>
        </tr>`).join('')}</tbody></table>`;
  } catch (e) { toast(e.message, 'error'); }
}

async function submitRule() {
  const keyword = document.getElementById('r-keyword').value.trim();
  const category_id = document.getElementById('r-category').value;
  const clean_merchant = document.getElementById('r-clean').value.trim();
  if (!keyword) { toast('Keyword is required', 'warning'); return; }
  try {
    await API.post('/api/rules', { keyword, category_id: +category_id, clean_merchant });
    toast('Rule added!', 'success');
    document.getElementById('r-keyword').value = '';
    document.getElementById('r-clean').value = '';
    loadRules();
  } catch (e) { toast(e.message, 'error'); }
}
