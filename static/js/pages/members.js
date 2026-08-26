// ── members.js ────────────────────────────────────────────────────────────
let _membersData = [];
let _banksData = [];
let _cardsData = [];
let _editingAccountId = null;

async function renderMembers() {
  const root = document.getElementById('page-root');
  root.innerHTML = `
    <div class="page-header fade-in">
      <h2>👥 Family Members & Banks</h2>
      <p>Manage household members, bank accounts, and linked cards auto-synced from statements</p>
    </div>
    <div class="page-content fade-in">
      <div class="grid-2">
        <!-- Household Members Column -->
        <div class="card">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
            <div class="card-title" style="margin-bottom:0">Household Members</div>
            <button class="btn btn-primary btn-sm" onclick="showAddMember()">+ Add Member</button>
          </div>
          <div id="members-list"><div class="skeleton" style="height:120px;border-radius:10px;"></div></div>
          
          <div id="add-member-form" style="display:none;margin-top:16px;padding:16px;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:10px">
            <div style="font-weight:600;color:var(--text-1);margin-bottom:12px">Add Household Member</div>
            <div class="form-group"><label>Full Name</label><input type="text" id="m-name" placeholder="e.g. Priya Sharma"></div>
            <div class="form-group"><label>Role</label><input type="text" id="m-role" placeholder="e.g. Primary Earner / Spouse" value="Member"></div>
            <div class="form-group"><label>Avatar Color</label><input type="color" id="m-color" value="#4F8EFF" style="width:60px;height:36px;padding:2px;cursor:pointer"></div>
            <div style="display:flex;gap:8px">
              <button class="btn btn-primary btn-sm" onclick="submitAddMember()">Save Member</button>
              <button class="btn btn-secondary btn-sm" onclick="document.getElementById('add-member-form').style.display='none'">Cancel</button>
            </div>
          </div>

          <div id="edit-member-form" style="display:none;margin-top:16px;padding:16px;background:rgba(79,142,255,0.06);border:1px solid rgba(79,142,255,0.25);border-radius:10px">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
              <div style="font-weight:700;color:var(--blue)">✏️ Update Member</div>
              <span id="edit-member-badge" style="font-size:.75rem;font-family:var(--mono);color:var(--text-3)"></span>
            </div>
            <div class="form-group"><label>Full Name</label><input type="text" id="edit-m-name" placeholder="e.g. Priya Sharma"></div>
            <div class="form-group"><label>Role</label><input type="text" id="edit-m-role" placeholder="e.g. Primary Earner / Spouse"></div>
            <div class="form-group"><label>Avatar Color</label><input type="color" id="edit-m-color" value="#4F8EFF" style="width:60px;height:36px;padding:2px;cursor:pointer"></div>
            <div style="display:flex;gap:8px;margin-top:10px">
              <button class="btn btn-primary btn-sm" onclick="submitEditMember()">Save Changes</button>
              <button class="btn btn-secondary btn-sm" onclick="cancelEditMember()">Cancel</button>
            </div>
          </div>
        </div>

        <!-- Banks & Cards Column -->
        <div class="card">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
            <div>
              <div class="card-title" style="margin-bottom:2px">Banks & Cards</div>
              <div style="font-size:.78rem;color:var(--text-3)">Auto-updated from statement uploads with live editing</div>
            </div>
            <button class="btn btn-primary btn-sm" onclick="showAddCard()">+ Add Card</button>
          </div>
          
          <div id="cards-list"><div class="skeleton" style="height:180px;border-radius:10px;"></div></div>

          <!-- Add Card Form -->
          <div id="add-card-form" style="display:none;margin-top:16px;padding:16px;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:10px">
            <div style="font-weight:600;color:var(--text-1);margin-bottom:12px">Link Bank Account or Card</div>
            <div class="form-group">
              <label>Bank</label>
              <select id="c-bank" style="width:100%"></select>
            </div>
            <div class="form-group">
              <label>Household Member</label>
              <select id="c-member" style="width:100%"></select>
            </div>
            <div class="form-group">
              <label>Card / Account Name</label>
              <input type="text" id="c-name" placeholder="e.g. HDFC Regalia Gold / SBI Cashback">
            </div>
            <div class="grid-2" style="gap:10px">
              <div class="form-group">
                <label>Account Type</label>
                <select id="c-type" style="width:100%">
                  <option value="Credit Card">Credit Card</option>
                  <option value="Savings Account">Savings Account</option>
                  <option value="Salary Account">Salary Account</option>
                </select>
              </div>
              <div class="form-group">
                <label>Last 4 Digits</label>
                <input type="text" id="c-last4" maxlength="4" placeholder="e.g. 4812">
              </div>
            </div>
            <div style="display:flex;gap:8px;margin-top:10px">
              <button class="btn btn-primary btn-sm" onclick="submitAddCard()">Save Card</button>
              <button class="btn btn-secondary btn-sm" onclick="document.getElementById('add-card-form').style.display='none'">Cancel</button>
            </div>
          </div>

          <!-- Edit Card Form -->
          <div id="edit-card-form" style="display:none;margin-top:16px;padding:16px;background:rgba(79,142,255,0.06);border:1px solid rgba(79,142,255,0.25);border-radius:10px">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
              <div style="font-weight:700;color:var(--blue)">✏️ Update Card Details</div>
              <span id="edit-card-badge" style="font-size:.75rem;font-family:var(--mono);color:var(--text-3)"></span>
            </div>
            <div class="form-group">
              <label>Card / Account Name</label>
              <input type="text" id="edit-c-name" placeholder="e.g. ICICI Amazon Pay Credit Card">
            </div>
            <div class="grid-2" style="gap:10px">
              <div class="form-group">
                <label>Bank</label>
                <select id="edit-c-bank" style="width:100%"></select>
              </div>
              <div class="form-group">
                <label>Household Member</label>
                <select id="edit-c-member" style="width:100%"></select>
              </div>
            </div>
            <div class="grid-2" style="gap:10px">
              <div class="form-group">
                <label>Account Type</label>
                <select id="edit-c-type" style="width:100%">
                  <option value="Credit Card">Credit Card</option>
                  <option value="Savings Account">Savings Account</option>
                  <option value="Salary Account">Salary Account</option>
                </select>
              </div>
              <div class="form-group">
                <label>Last 4 Digits</label>
                <input type="text" id="edit-c-last4" maxlength="4" placeholder="e.g. 2002">
              </div>
            </div>
            <div style="display:flex;gap:8px;margin-top:12px">
              <button class="btn btn-primary btn-sm" onclick="submitEditCard()">Save Changes</button>
              <button class="btn btn-secondary btn-sm" onclick="cancelEditCard()">Cancel</button>
            </div>
          </div>
        </div>
      </div>
    </div>`;

  await Promise.all([loadMembers(), loadCards()]);
}

async function loadMembers() {
  try {
    _membersData = await API.get('/api/members');
    const el = document.getElementById('members-list');
    if (!el) return;
    if (!_membersData.length) { el.innerHTML = '<p style="color:var(--text-3);font-size:.85rem">No members found.</p>'; return; }
    el.innerHTML = _membersData.map(m => {
      const txCount = Number(m.transaction_count || 0);
      const canDelete = txCount === 0;
      return `
        <div class="member-card" style="margin-bottom:10px">
          <div class="member-avatar" style="background:${m.avatar_color||'#4F8EFF'}">${(m.member_name||'?')[0]}</div>
          <div style="flex:1">
            <div style="font-weight:600;color:var(--text-1)">${escapeHtml(m.member_name)}</div>
            <div style="font-size:.78rem;color:var(--text-3)">${escapeHtml(m.role)}</div>
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <button class="btn btn-secondary btn-sm" onclick="showEditMember(${m.member_id})" title="Edit member details" style="padding:4px 8px">✏️</button>
            ${txCount > 0
              ? `<button class="btn btn-secondary btn-sm" disabled style="opacity:0.35;cursor:not-allowed" title="Cannot delete: ${txCount} transaction${txCount !== 1 ? 's' : ''} linked to this member">🔒</button>`
              : `<button class="btn btn-danger btn-sm" onclick="deleteMember(${m.member_id},'${escapeHtml(m.member_name)}')">🗑️</button>`
            }
          </div>
        </div>`;
    }).join('');
  } catch (e) { toast(e.message, 'error'); }
}

async function loadCards() {
  try {
    _cardsData = await API.get('/api/members/cards');
    const el = document.getElementById('cards-list');
    if (!el) return;
    if (!_cardsData.length) { el.innerHTML = '<p style="color:var(--text-3);font-size:.85rem">No cards found. Upload statements to auto-detect and register cards.</p>'; return; }
    
    el.innerHTML = _cardsData.map(c => {
      const txCount = c.tx_count || 0;
      const maskedLast4 = c.last4 ? `•••• ${escapeHtml(c.last4)}` : '•••• ••••';
      const canDelete = txCount === 0;

      return `
        <div style="display:flex;align-items:center;gap:12px;padding:12px 14px;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:10px;margin-bottom:10px">
          <span style="font-size:1.3rem">${c.bank_icon || c.icon || '💳'}</span>
          <div style="flex:1;min-width:0">
            <div style="font-weight:600;font-size:.875rem;color:var(--text-1);text-overflow:ellipsis;white-space:nowrap;overflow:hidden">${escapeHtml(c.account_name)}</div>
            <div style="font-size:.75rem;color:var(--text-3);margin-top:2px">
              ${escapeHtml(c.bank_name)} · ${escapeHtml(c.account_type)} · <span style="font-family:var(--mono);color:var(--blue);font-weight:600">${maskedLast4}</span>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <span class="badge badge-blue" style="font-size:.72rem">👤 ${escapeHtml(c.member_name)}</span>
            ${txCount > 0 ? `<span class="badge badge-green" style="font-size:.72rem">${txCount} txns</span>` : `<span class="badge badge-amber" style="font-size:.72rem">0 txns</span>`}
            
            <button class="btn btn-secondary btn-sm" onclick="showEditCard('${escapeHtml(c.account_id)}')" title="Edit card name, last 4 digits, bank or member" style="padding:4px 8px">✏️</button>
            
            ${canDelete 
              ? `<button class="btn btn-danger btn-sm" onclick="deleteCard('${escapeHtml(c.account_id)}', '${escapeHtml(c.account_name)}')" title="Delete Card (0 transactions linked)">🗑️</button>`
              : `<button class="btn btn-secondary btn-sm" disabled style="opacity:0.35;cursor:not-allowed" title="Cannot delete: ${txCount} transactions linked to this card">🔒</button>`
            }
          </div>
        </div>`;
    }).join('');
  } catch (e) { toast(e.message, 'error'); }
}

function showAddMember() {
  document.getElementById('add-member-form').style.display = 'block';
  document.getElementById('m-name').focus();
}

async function submitAddMember() {
  const name = document.getElementById('m-name').value.trim();
  const role = document.getElementById('m-role').value.trim();
  const color = document.getElementById('m-color').value;
  if (!name) { toast('Name is required', 'warning'); return; }
  try {
    await API.post('/api/members', { name, role, color });
    toast(`${name} added!`, 'success');
    document.getElementById('add-member-form').style.display = 'none';
    await loadMembers();
  } catch (e) { toast(e.message, 'error'); }
}

let _editingMemberId = null;

function showEditMember(memberId) {
  document.getElementById('add-member-form').style.display = 'none';
  const member = _membersData.find(m => Number(m.member_id) === Number(memberId));
  if (!member) return;

  _editingMemberId = Number(memberId);
  const form = document.getElementById('edit-member-form');
  form.style.display = 'block';
  document.getElementById('edit-member-badge').textContent = `ID: ${memberId}`;
  document.getElementById('edit-m-name').value = member.member_name || '';
  document.getElementById('edit-m-role').value = member.role || 'Member';
  document.getElementById('edit-m-color').value = member.avatar_color || '#4F8EFF';
  document.getElementById('edit-m-name').focus();
}

function cancelEditMember() {
  _editingMemberId = null;
  document.getElementById('edit-member-form').style.display = 'none';
}

async function submitEditMember() {
  if (!_editingMemberId) return;

  const name = document.getElementById('edit-m-name').value.trim();
  const role = document.getElementById('edit-m-role').value.trim();
  const color = document.getElementById('edit-m-color').value;

  if (!name) { toast('Name is required', 'warning'); return; }

  try {
    await API.patch(`/api/members/${_editingMemberId}`, { name, role, color });
    toast('Member updated successfully!', 'success');
    cancelEditMember();
    await loadMembers();
  } catch (e) { toast(e.message, 'error'); }
}

async function deleteMember(id, name) {
  const member = _membersData.find(m => Number(m.member_id) === Number(id));
  const txCount = Number(member?.transaction_count || 0);
  if (txCount > 0) {
    toast(`Cannot delete ${name}: ${txCount} transaction${txCount !== 1 ? 's are' : ' is'} linked to this member.`, 'warning');
    return;
  }

  if (!confirm(`Remove ${name} from the household?`)) return;
  try {
    await API.delete(`/api/members/${id}`);
    toast(`${name} removed`, 'success');
    await loadMembers();
  } catch (e) { toast(e.message, 'error'); }
}

async function showAddCard() {
  document.getElementById('edit-card-form').style.display = 'none';
  const form = document.getElementById('add-card-form');
  form.style.display = 'block';

  try {
    if (!_banksData.length) _banksData = await API.get('/api/members/banks');
    const bankSel = document.getElementById('c-bank');
    bankSel.innerHTML = _banksData.map(b => `<option value="${b.bank_id}" data-code="${b.bank_code}">${b.icon||'🏛️'} ${escapeHtml(b.bank_name)}</option>`).join('');

    const memSel = document.getElementById('c-member');
    memSel.innerHTML = _membersData.map(m => `<option value="${m.member_id}">👤 ${escapeHtml(m.member_name)}</option>`).join('');
  } catch {}
}

async function submitAddCard() {
  const bankSel = document.getElementById('c-bank');
  const bankId = bankSel.value;
  const opt = bankSel.options[bankSel.selectedIndex];
  const bankCode = opt ? opt.dataset.code : 'GENERIC';
  const memberId = document.getElementById('c-member').value;
  const name = document.getElementById('c-name').value.trim();
  const accType = document.getElementById('c-type').value;
  const last4 = document.getElementById('c-last4').value.trim();

  if (!name) { toast('Card / Account name is required', 'warning'); return; }
  
  const cleanLast4 = last4.replace(/[^0-9]/g, '');
  const accountId = `${bankCode.toLowerCase()}_${name.toLowerCase().replace(/[^a-z0-9]/g, '_')}_${cleanLast4 || '1'}`;

  try {
    await API.post('/api/members/cards', {
      account_id: accountId,
      name: name,
      bank_id: +bankId,
      member_id: +memberId,
      account_type: accType,
      last4: cleanLast4,
      credit_limit: 100000.0
    });
    toast(`Card '${name}' added!`, 'success');
    document.getElementById('add-card-form').style.display = 'none';
    await loadCards();
  } catch (e) { toast(e.message, 'error'); }
}

async function showEditCard(accountId) {
  document.getElementById('add-card-form').style.display = 'none';
  const card = _cardsData.find(c => c.account_id === accountId);
  if (!card) return;

  _editingAccountId = accountId;
  const form = document.getElementById('edit-card-form');
  form.style.display = 'block';

  document.getElementById('edit-card-badge').textContent = `ID: ${accountId}`;
  document.getElementById('edit-c-name').value = card.account_name || '';
  document.getElementById('edit-c-last4').value = card.last4 || '';
  document.getElementById('edit-c-type').value = card.account_type || 'Credit Card';

  try {
    if (!_banksData.length) _banksData = await API.get('/api/members/banks');
    const bankSel = document.getElementById('edit-c-bank');
    bankSel.innerHTML = _banksData.map(b => `<option value="${b.bank_id}">${b.icon||'🏛️'} ${escapeHtml(b.bank_name)}</option>`).join('');
    bankSel.value = card.bank_id;

    const memSel = document.getElementById('edit-c-member');
    memSel.innerHTML = _membersData.map(m => `<option value="${m.member_id}">👤 ${escapeHtml(m.member_name)}</option>`).join('');
    memSel.value = card.member_id;
  } catch {}

  document.getElementById('edit-c-name').focus();
}

function cancelEditCard() {
  _editingAccountId = null;
  document.getElementById('edit-card-form').style.display = 'none';
}

async function submitEditCard() {
  if (!_editingAccountId) return;

  const name = document.getElementById('edit-c-name').value.trim();
  const last4 = document.getElementById('edit-c-last4').value.trim();
  const bankId = document.getElementById('edit-c-bank').value;
  const memberId = document.getElementById('edit-c-member').value;
  const accType = document.getElementById('edit-c-type').value;

  if (!name) { toast('Card / Account name is required', 'warning'); return; }

  const cleanLast4 = last4.replace(/[^0-9]/g, '');

  try {
    const res = await API.patch(`/api/members/cards/${_editingAccountId}`, {
      account_name: name,
      last4: cleanLast4,
      bank_id: +bankId,
      member_id: +memberId,
      account_type: accType
    });
    toast('Card details updated successfully!', 'success');
    cancelEditCard();
    await loadCards();
  } catch (e) {
    toast('Failed to update card: ' + e.message, 'error');
  }
}

async function deleteCard(accountId, cardName) {
  if (!confirm(`Delete card '${cardName}'? This action cannot be undone.`)) return;
  try {
    const res = await API.delete(`/api/members/cards/${accountId}`);
    toast(`Card '${cardName}' deleted successfully`, 'success');
    await loadCards();
  } catch (e) {
    toast(e.message, 'error');
  }
}


