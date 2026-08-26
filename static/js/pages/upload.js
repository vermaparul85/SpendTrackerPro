// ── upload.js ─────────────────────────────────────────────────────────────
let _selectedFile = null;
let _inspectData = null;
let _cardsList = [];
let _membersList = [];

async function renderUpload() {
  try {
    const [cards, members] = await Promise.all([
      API.get('/api/members/cards'),
      API.get('/api/members')
    ]);
    _cardsList = cards || [];
    _membersList = members || [];
  } catch {
    _cardsList = [];
    _membersList = [];
  }

  const memberOptions = _membersList.map(m => `<option value="${m.member_id}">👤 ${escapeHtml(m.member_name)} (${escapeHtml(m.role)})</option>`).join('');

  const root = document.getElementById('page-root');
  root.innerHTML = `
    <div class="page-header fade-in">
      <h2>📤 Upload Statements</h2>
      <p>Automatic bank & member recognition with encrypted statement password support</p>
    </div>
    <div class="page-content fade-in">
      <div class="grid-2">
        <!-- ── Left Column: Upload & Auto-Detection Card ── -->
        <div class="card">
          <div class="card-title">Statement Ingestion</div>
          
          <!-- Drop Zone -->
          <div class="drop-zone" id="drop-zone" onclick="document.getElementById('pdf-file').click()">
            <div class="drop-icon">📄</div>
            <h3>Drop statement PDF / CSV here or click to browse</h3>
            <p>Smart auto-detection for HDFC, ICICI, SBI, Axis, AMEX, Kotak, CRED, BOB & more</p>
          </div>
          <input type="file" id="pdf-file" accept=".pdf,.csv" style="display:none" onchange="handleFileSelect(event)" />

          <!-- Selected File Header -->
          <div id="file-selected" style="margin-top:14px;display:none">
            <div style="display:flex;align-items:center;gap:12px;padding:12px 16px;background:rgba(79,142,255,0.08);border:1px solid rgba(79,142,255,0.2);border-radius:10px">
              <span style="font-size:1.4rem" id="file-icon">📄</span>
              <div style="flex:1;overflow:hidden">
                <div id="file-name" style="font-size:.9rem;font-weight:600;color:var(--text-1);text-overflow:ellipsis;white-space:nowrap;overflow:hidden"></div>
                <div id="file-meta" style="font-size:.75rem;color:var(--text-3);margin-top:2px"></div>
              </div>
              <button class="btn btn-secondary btn-sm" onclick="clearSelectedFile(event)">✕</button>
            </div>
          </div>

          <!-- Auto-Detection Card -->
          <div id="detection-card" style="margin-top:14px;display:none;padding:16px;background:rgba(17,27,52,0.9);border:1px solid rgba(79,142,255,0.25);border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.3)">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
              <div style="font-size:.78rem;font-weight:700;letter-spacing:.08em;color:var(--blue);text-transform:uppercase">
                ✨ Auto-Detected Details
              </div>
              <span id="badge-confidence" class="badge badge-green">High Confidence</span>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px">
              <div style="padding:10px 12px;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:8px">
                <div style="font-size:.7rem;color:var(--text-3);text-transform:uppercase;font-weight:600">Bank</div>
                <div id="detect-bank" style="font-size:.875rem;font-weight:600;color:var(--text-1);margin-top:2px">🏛️ Detecting...</div>
              </div>
              <div style="padding:10px 12px;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:8px">
                <div style="font-size:.7rem;color:var(--text-3);text-transform:uppercase;font-weight:600;margin-bottom:3px">Assigned Member</div>
                <select id="detect-member-select" style="width:100%;background:var(--bg-2);border:1px solid var(--border);color:var(--text-1);border-radius:6px;padding:4px 8px;font-size:.82rem;font-weight:600;outline:none">
                  ${memberOptions}
                </select>
              </div>
            </div>

            <div style="padding:10px 12px;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:8px;margin-bottom:12px">
              <div style="font-size:.7rem;color:var(--text-3);text-transform:uppercase;font-weight:600">Mapped Card / Account</div>
              <div id="detect-card" style="font-size:.875rem;font-weight:600;color:var(--text-1);margin-top:2px">💳 Detecting...</div>
            </div>

            <!-- Password Protected Section -->
            <div id="password-section" style="display:none;margin-top:12px;padding:14px;background:rgba(255,186,59,0.08);border:1px solid rgba(255,186,59,0.25);border-radius:10px">
              <div style="display:flex;align-items:center;gap:8px;font-weight:600;color:var(--amber);margin-bottom:6px">
                <span>🔒</span> Password-Protected Statement
              </div>
              <div style="font-size:.78rem;color:var(--text-2);margin-bottom:10px">
                This PDF is encrypted by the bank. Enter your password to unlock:
              </div>
              <div style="display:flex;gap:8px">
                <input type="password" id="statement-password" placeholder="e.g. DOB (DDMMYYYY) or PAN" style="flex:1" onkeydown="if(event.key==='Enter') testUnlockPassword()" />
                <button class="btn btn-secondary btn-sm" onclick="togglePasswordVisibility()">👁️</button>
                <button class="btn btn-primary btn-sm" onclick="testUnlockPassword()">Unlock</button>
              </div>
              <div style="font-size:.72rem;color:var(--text-3);margin-top:6px">
                💡 Common formats: <strong>DOB (DDMMYYYY)</strong>, <strong>Name (4 chars) + DOB (DDMM)</strong>, or <strong>PAN Card</strong>
              </div>
            </div>

            <!-- Optional Manual Override Toggle -->
            <div style="margin-top:12px">
              <a href="javascript:void(0)" onclick="toggleOverrideSection()" style="font-size:.78rem;color:var(--blue);text-decoration:none">
                ⚙️ Need to adjust bank, card name, or last 4 digits? (Optional Override)
              </a>
              <div id="override-section" style="display:none;margin-top:10px;padding:12px;background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:8px">
                <div class="form-group" style="margin-bottom:10px">
                  <label style="font-size:.72rem">Select Existing Card (Optional)</label>
                  <select id="sel-account-override" onchange="applySelectedOverrideCard()" style="font-size:.82rem;padding:6px 10px;width:100%">
                    <option value="">Auto (Create / Match from Statement)</option>
                    ${_cardsList.map(c => `<option value="${c.account_id}" data-bank="${c.bank_code}" data-member="${c.member_id}" data-name="${escapeHtml(c.account_name || '')}" data-last4="${escapeHtml(c.last4 || '')}">${c.icon||'💳'} ${escapeHtml(c.account_name)} (${escapeHtml(c.member_name)})</option>`).join('')}
                  </select>
                </div>
                <div class="grid-2" style="gap:10px;margin-bottom:4px">
                  <div class="form-group">
                    <label style="font-size:.72rem">Correct Card / Account Name</label>
                    <input type="text" id="override-card-name" placeholder="e.g. SBI SimplyClick / HDFC Regalia" style="font-size:.82rem;padding:6px 10px" />
                  </div>
                  <div class="form-group">
                    <label style="font-size:.72rem">Correct Last 4 Digits</label>
                    <input type="text" id="override-card-last4" maxlength="4" placeholder="e.g. 2002" style="font-size:.82rem;padding:6px 10px" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Upload Progress Animation -->
          <div id="upload-progress" style="display:none;margin-top:14px;margin-bottom:12px">
            <div class="progress-wrap"><div class="progress-fill" id="progress-fill" style="width:0%"></div></div>
            <div style="font-size:.78rem;color:var(--text-2);margin-top:6px" id="progress-label">Inspecting & Parsing...</div>
          </div>

          <!-- Main Submit Button -->
          <button class="btn btn-primary btn-full" id="btn-upload" style="margin-top:14px" onclick="submitUpload()" disabled>
            ✨ Ingest Statement
          </button>
          
          <div id="upload-result" style="margin-top:14px"></div>
        </div>

        <!-- ── Right Column: Quick Demo & History ── -->
        <div class="card">
          <div class="card-title">Quick Actions & Testing</div>
          <div style="display:flex;flex-direction:column;gap:12px;margin-top:8px">
            <div style="padding:16px;background:rgba(255,91,127,0.06);border:1px solid rgba(255,91,127,0.15);border-radius:10px">
              <div style="font-weight:600;color:var(--text-1);margin-bottom:4px">🗑️ Reset Database</div>
              <div style="font-size:.82rem;color:var(--text-2);margin-bottom:12px">Clear all ingested statements & transactions for a fresh start.</div>
              <button class="btn btn-danger btn-sm" onclick="resetDatabase()">Reset All Data</button>
            </div>
          </div>

          <div style="margin-top:24px">
            <div class="card-title">Recent Upload History & Member Assignment</div>
            <div id="upload-history" class="table-wrap">
              <div class="skeleton" style="height:120px;border-radius:8px;"></div>
            </div>
          </div>
        </div>
      </div>
    </div>`;

  setupDropZone();
  loadUploadHistory();
}

function setupDropZone() {
  const zone = document.getElementById('drop-zone');
  if (!zone) return;
  ['dragenter', 'dragover'].forEach(e => zone.addEventListener(e, ev => { ev.preventDefault(); zone.classList.add('drag-over'); }));
  ['dragleave', 'drop'].forEach(e => zone.addEventListener(e, ev => { ev.preventDefault(); zone.classList.remove('drag-over'); }));
  zone.addEventListener('drop', ev => {
    const file = ev.dataTransfer.files[0];
    if (file) handleFileChosen(file);
  });
}

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) handleFileChosen(file);
}

function clearSelectedFile(e) {
  if (e) e.stopPropagation();
  _selectedFile = null;
  _inspectData = null;
  document.getElementById('pdf-file').value = '';
  document.getElementById('file-selected').style.display = 'none';
  document.getElementById('detection-card').style.display = 'none';
  document.getElementById('password-section').style.display = 'none';
  document.getElementById('upload-result').innerHTML = '';
  document.getElementById('btn-upload').disabled = true;
}

async function handleFileChosen(file) {
  _selectedFile = file;
  _inspectData = null;

  document.getElementById('file-selected').style.display = 'block';
  document.getElementById('file-name').textContent = file.name;
  document.getElementById('file-meta').textContent = `${(file.size / 1024).toFixed(1)} KB · PDF/CSV`;
  document.getElementById('file-icon').textContent = file.name.toLowerCase().endsWith('.csv') ? '📊' : '📄';

  // Show detection card with loading placeholders
  const dCard = document.getElementById('detection-card');
  dCard.style.display = 'block';
  document.getElementById('detect-bank').innerHTML = `<span class="skeleton" style="display:inline-block;width:100px;height:18px"></span>`;
  document.getElementById('detect-card').innerHTML = `<span class="skeleton" style="display:inline-block;width:140px;height:18px"></span>`;
  document.getElementById('password-section').style.display = 'none';
  document.getElementById('btn-upload').disabled = true;

  await runInspection();
}

async function runInspection(password = null) {
  if (!_selectedFile) return;

  const fd = new FormData();
  fd.append('file', _selectedFile);
  if (password) fd.append('password', password);

  try {
    const res = await API.uploadForm('/api/upload/inspect', fd);
    _inspectData = res;

    // Render detected bank & member
    const bankEl = document.getElementById('detect-bank');
    bankEl.innerHTML = `${res.bank_icon || '🏛️'} <strong>${res.bank_name || 'Generic Bank'}</strong> <span style="font-size:.75rem;color:var(--text-3)">(${res.bank_code})</span>`;

    const memberSelect = document.getElementById('detect-member-select');
    if (memberSelect && res.member_id) {
      memberSelect.value = res.member_id;
    }

    const cardEl = document.getElementById('detect-card');
    const last4Str = res.masked_last4 || (res.last4 ? `•••• ${res.last4}` : '•••• ••••');
    cardEl.innerHTML = `💳 <strong>${res.account_name || (res.bank_code + ' Account')}</strong> <span style="font-size:.82rem;color:var(--blue);font-family:var(--mono);margin-left:6px">${last4Str}</span>`;

    const confBadge = document.getElementById('badge-confidence');
    confBadge.className = res.status === 'OK' ? 'badge badge-green' : 'badge badge-amber';
    confBadge.textContent = res.status === 'OK' ? '✨ Auto-Detected' : (res.is_encrypted ? '🔒 Password Required' : 'Scan Complete');

    // Handle Password Protection
    const pwdSection = document.getElementById('password-section');
    const uploadBtn = document.getElementById('btn-upload');

    if (res.is_encrypted && res.status !== 'OK') {
      pwdSection.style.display = 'block';
      uploadBtn.disabled = true;
      uploadBtn.textContent = '🔒 Unlock Password to Ingest';
      toast('Statement is password-protected. Please enter password.', 'warning');
    } else {
      if (res.status === 'OK' && password) {
        pwdSection.style.display = 'block';
        toast('Password unlocked successfully!', 'success');
      }
      uploadBtn.disabled = false;
      uploadBtn.textContent = '✨ Ingest Statement';
    }

    // Auto-select in override dropdown if matched
    const overrideSel = document.getElementById('sel-account-override');
    if (overrideSel && res.account_id) {
      overrideSel.value = res.account_id;
      applySelectedOverrideCard();
    } else {
      // Pre-populate custom card name & last4 in override section
      const overrideCardName = document.getElementById('override-card-name');
      if (overrideCardName && res.account_name) {
        overrideCardName.value = res.account_name;
      }
      const overrideLast4 = document.getElementById('override-card-last4');
      if (overrideLast4 && res.last4) {
        overrideLast4.value = res.last4;
      }
    }

  } catch (e) {
    toast('Error scanning statement: ' + e.message, 'error');
  }
}

async function testUnlockPassword() {
  const pwdInput = document.getElementById('statement-password');
  const pwd = pwdInput ? pwdInput.value.trim() : '';
  if (!pwd) {
    toast('Please enter the statement password', 'warning');
    return;
  }
  await runInspection(pwd);
}

function togglePasswordVisibility() {
  const input = document.getElementById('statement-password');
  if (input) input.type = input.type === 'password' ? 'text' : 'password';
}

function applySelectedOverrideCard() {
  const sel = document.getElementById('sel-account-override');
  const nameInput = document.getElementById('override-card-name');
  const last4Input = document.getElementById('override-card-last4');
  if (!sel || !nameInput || !last4Input) return;

  const selected = sel.value;
  if (!selected) {
    const detectedName = _inspectData?.account_name || '';
    const detectedLast4 = _inspectData?.last4 || '';
    if (detectedName && !nameInput.value.trim()) nameInput.value = detectedName;
    if (detectedLast4 && !last4Input.value.trim()) last4Input.value = detectedLast4;
    return;
  }

  const opt = sel.options[sel.selectedIndex];
  const selectedName = opt?.dataset?.name || '';
  const selectedLast4 = opt?.dataset?.last4 || '';

  if (selectedName) nameInput.value = selectedName;
  if (selectedLast4) last4Input.value = selectedLast4;
}

function toggleOverrideSection() {
  const el = document.getElementById('override-section');
  if (el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

async function submitUpload() {
  if (!_selectedFile) {
    toast('Please select a statement file first', 'warning');
    return;
  }

  const fd = new FormData();
  fd.append('file', _selectedFile);

  // Explicit member selection from detection card
  const memberSel = document.getElementById('detect-member-select');
  if (memberSel && memberSel.value) {
    fd.append('member_id', memberSel.value);
  }

  // Check if custom card name & last 4 provided
  const customName = document.getElementById('override-card-name');
  if (customName && customName.value.trim()) {
    fd.append('card_name', customName.value.trim());
  }
  const customLast4 = document.getElementById('override-card-last4');
  if (customLast4 && customLast4.value.trim()) {
    fd.append('last4', customLast4.value.trim());
  }

  // Check if password provided
  const pwdInput = document.getElementById('statement-password');
  if (pwdInput && pwdInput.value.trim()) {
    fd.append('password', pwdInput.value.trim());
  }

  // Check if user manually overrode account
  const overrideSel = document.getElementById('sel-account-override');
  if (overrideSel && overrideSel.value) {
    const opt = overrideSel.options[overrideSel.selectedIndex];
    fd.append('account_id', opt.value);
    if (opt.dataset.bank) fd.append('bank_code', opt.dataset.bank);
    if (opt.dataset.member) fd.append('member_id', opt.dataset.member);
  }

  // Show progress animation
  const progEl = document.getElementById('upload-progress');
  const progFill = document.getElementById('progress-fill');
  const progLbl = document.getElementById('progress-label');
  const btn = document.getElementById('btn-upload');

  progEl.style.display = 'block';
  progFill.style.width = '45%';
  progLbl.textContent = 'Decrypting & parsing statement...';
  btn.disabled = true;

  try {
    const res = await API.uploadForm('/api/upload', fd);

    progFill.style.width = '100%';
    progLbl.textContent = 'Ingestion complete!';

    document.getElementById('upload-result').innerHTML = `
      <div style="padding:14px 18px;background:rgba(0,209,140,0.08);border:1px solid rgba(0,209,140,0.25);border-radius:10px;font-size:.875rem">
        <div style="display:flex;align-items:center;gap:8px;font-weight:700;color:var(--emerald);margin-bottom:6px">
          <span>✅</span> Ingested ${res.inserted} Transactions (${formatINR(res.total_debit)})
        </div>
        <div style="font-size:.8rem;color:var(--text-2);line-height:1.5">
          Bank: <strong>${res.auto_detected?.bank_name}</strong> · Member: <strong>${res.auto_detected?.member_name}</strong> · Card: <strong>${res.auto_detected?.account_name}</strong>
        </div>
      </div>`;

    toast(`Successfully ingested ${res.inserted} transactions!`, 'success');
    loadUploadHistory();
  } catch (e) {
    progFill.style.width = '0%';
    document.getElementById('upload-result').innerHTML = `
      <div style="padding:14px;background:rgba(255,91,127,0.08);border:1px solid rgba(255,91,127,0.25);border-radius:10px;font-size:.875rem;color:var(--rose)">
        ❌ <strong>Error:</strong> ${e.message}
      </div>`;
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
    setTimeout(() => { progEl.style.display = 'none'; }, 2500);
  }
}

async function loadSampleData() {
  const btn = document.getElementById('btn-sample');
  btn.disabled = true;
  btn.textContent = '⏳ Ingesting sample bundle...';
  try {
    const res = await API.post('/api/upload/sample', {});
    toast(res.message, 'success');
    loadUploadHistory();
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Load Sample Data';
  }
}

async function resetDatabase() {
  if (!confirm('Are you sure you want to reset ALL statement data and transaction records?')) return;
  try {
    await API.post('/api/upload/reset', {});
    toast('Database reset successfully', 'success');
    loadUploadHistory();
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function loadUploadHistory() {
  const el = document.getElementById('upload-history');
  if (!el) return;
  try {
    const stmts = await API.get('/api/rules/statements');
    if (!stmts.length) {
      el.innerHTML = '<p style="font-size:.82rem;color:var(--text-3);padding:12px 0">No statements uploaded yet.</p>';
      return;
    }
    const memOptions = _membersList.map(m => `<option value="${m.member_id}">👤 ${escapeHtml(m.member_name)}</option>`).join('');

    el.innerHTML = `<table>
      <thead><tr><th>File</th><th>Bank</th><th>Records</th><th>Debits</th><th>Household Member</th><th>Date</th><th></th></tr></thead>
      <tbody>${stmts.map(s => `
        <tr>
          <td style="font-size:.8rem;max-width:130px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escapeHtml(s.filename)}">
            📄 ${escapeHtml(s.filename)}
          </td>
          <td><span class="badge badge-blue">${escapeHtml(s.bank_code)}</span></td>
          <td style="font-family:var(--mono);font-size:.8rem">${s.record_count}</td>
          <td class="amount-debit" style="font-size:.8rem">${formatINR(s.total_debit)}</td>
          <td>
            <select class="stmt-member-select" data-upload="${s.upload_id}" style="background:transparent;border:1px solid var(--border);color:var(--text-2);border-radius:6px;padding:3px 6px;font-size:.78rem;cursor:pointer;outline:none">
              ${memOptions}
            </select>
          </td>
          <td style="font-size:.75rem;color:var(--text-3)">${s.uploaded_at?.slice(0, 10) || ''}</td>
          <td><button class="btn btn-danger btn-sm stmt-delete" data-upload="${s.upload_id}" data-filename="${escapeHtml(s.filename)}" title="Delete statement and related transactions">🗑️</button></td>
        </tr>`).join('')}</tbody></table>`;

    // Set current member value and attach change handler for instant statement reassignment
    el.querySelectorAll('.stmt-member-select').forEach(sel => {
      const stmt = stmts.find(s => s.upload_id === sel.dataset.upload);
      if (stmt && stmt.member_id) sel.value = stmt.member_id;
      sel.addEventListener('change', async () => {
        try {
          const res = await API.patch(`/api/upload/${sel.dataset.upload}/member`, { member_id: +sel.value });
          toast(`Reassigned all transactions to ${res.member_name}!`, 'success');
        } catch (e) {
          toast('Failed to reassign: ' + e.message, 'error');
        }
      });
    });

    el.querySelectorAll('.stmt-delete').forEach(btn => {
      btn.addEventListener('click', () => deleteStatement(btn.dataset.upload, btn.dataset.filename));
    });
  } catch {}
}

async function deleteStatement(uploadId, filename) {
  if (!confirm(`Delete "${filename}" and all transactions from this statement?`)) return;
  try {
    const res = await API.delete(`/api/upload/${encodeURIComponent(uploadId)}`);
    toast(`Deleted statement and ${res.deleted_transactions} related transactions.`, 'success');
    loadUploadHistory();
  } catch (e) {
    toast('Failed to delete statement: ' + e.message, 'error');
  }
}
