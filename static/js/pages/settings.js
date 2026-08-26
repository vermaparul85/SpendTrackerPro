// ── settings.js ───────────────────────────────────────────────────────────
async function renderSettings() {
  const root = document.getElementById('page-root');
  root.innerHTML = `
    <div class="page-header fade-in">
      <h2>⚙️ Settings</h2>
      <p>Configure your Gemini API key, database mode, and preferences</p>
    </div>
    <div class="page-content fade-in">
      <div class="grid-2">
        <div class="card">
          <div class="card-title">AI Configuration</div>
          <div class="form-group">
            <label>Gemini API Key</label>
            <div style="padding:12px 14px;background:rgba(79,142,255,0.06);border:1px solid rgba(79,142,255,0.16);border-radius:10px;font-size:.8rem;color:var(--text-2);line-height:1.5">
              Generate a Gemini API key from below link and store in the server environment file (.env).
              <div style="margin-top:8px"><a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:var(--blue)">Generate a Gemini API key</a></div>
            </div>
          </div>
          <div class="form-group">
            <label>Gemini Model</label>
            <select id="s-model">
              <option value="gemini-3.6-flash">gemini-3.6-flash</option>
              <option value="gemini-3.5-flash">gemini-3.5-flash</option>
              <option value="gemini-3.5-flash-lite">gemini-3.5-flash-lite</option>
            </select>
          </div>
          <button class="btn btn-primary btn-full" onclick="saveSettings()">💾 Save Settings</button>
          <div id="settings-status" style="margin-top:10px"></div>
        </div>
        <div class="card">
          <div class="card-title">Database Mode</div>
          <div style="display:flex;flex-direction:column;gap:10px;margin-top:4px">
            <label style="display:flex;align-items:flex-start;gap:12px;padding:14px;background:rgba(79,142,255,0.06);border:1px solid rgba(79,142,255,0.15);border-radius:10px;cursor:pointer">
              <input type="radio" name="db-mode" value="local" id="mode-local" style="margin-top:3px;width:auto;accent-color:var(--blue)">
              <div>
                <div style="font-weight:600;color:var(--text-1)">⚡ Local SQLite Mode</div>
                <div style="font-size:.8rem;color:var(--text-2);margin-top:2px">Data stored locally in <code style="font-family:var(--mono)">spend_tracker.db</code>. Privacy-first, no cloud required.</div>
              </div>
            </label>
            <label style="display:flex;align-items:flex-start;gap:12px;padding:14px;background:rgba(167,139,250,0.06);border:1px solid rgba(167,139,250,0.15);border-radius:10px;cursor:pointer">
              <input type="radio" name="db-mode" value="bigquery" id="mode-bq" style="margin-top:3px;width:auto;accent-color:var(--purple)">
              <div>
                <div style="font-weight:600;color:var(--text-1)">☁️ Google BigQuery Mode</div>
                <div style="font-size:.8rem;color:var(--text-2);margin-top:2px">Enterprise-scale analytics. Requires GCP project and credentials.</div>
              </div>
            </label>
          </div>
          <div style="margin-top:16px" id="bq-fields" style="display:none">
            <div class="form-group"><label>BigQuery Dataset ID</label><input type="text" id="s-dataset-id" placeholder="spend_tracker"></div>
          </div>
          <div style="margin-top:20px;padding:14px;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:10px">
            <div class="card-title" style="margin-bottom:8px">About SpendTracker Pro</div>
            <div style="font-size:.8rem;color:var(--text-2);line-height:1.6">
              <div>🔐 Privacy-first — all processing runs locally</div>
              <div>🤖 ADK 2.7.1 + Gemini model selection</div>
              <div>⚡ FastAPI + Chart.js + Vanilla JS</div>
              <div>🏦 Supports HDFC, ICICI, SBI, Axis, AMEX, Kotak</div>
            </div>
          </div>
        </div>
      </div>
    </div>`;

  // Load current settings
  try {
    const s = await API.get('/api/settings');
    const modelSel = document.getElementById('s-model');
    if (modelSel && s.gemini_model) modelSel.value = s.gemini_model;
    const modeLocal = document.getElementById('mode-local');
    const modeBQ = document.getElementById('mode-bq');
    if (s.db_mode === 'bigquery' && modeBQ) {
      modeBQ.checked = true;
      document.getElementById('bq-fields').style.display = 'block';
    } else if (modeLocal) {
      modeLocal.checked = true;
    }
    if (s.dataset_id) document.getElementById('s-dataset-id').value = s.dataset_id;
  } catch {}

  // Toggle BigQuery fields
  document.querySelectorAll('input[name="db-mode"]').forEach(r => {
    r.addEventListener('change', () => {
      const bqFields = document.getElementById('bq-fields');
      if (bqFields) bqFields.style.display = r.value === 'bigquery' ? 'block' : 'none';
    });
  });
}

async function saveSettings() {
  const body = {
    gemini_model: document.getElementById('s-model').value,
    db_mode: document.querySelector('input[name="db-mode"]:checked')?.value || 'local',
    dataset_id: document.getElementById('s-dataset-id')?.value.trim() || 'spend_tracker',
  };

  try {
    await API.post('/api/settings', body);
    toast('Settings saved!', 'success');
    const el = document.getElementById('settings-status');
    if (el) el.innerHTML = `<div class="badge badge-green">✓ Settings saved successfully</div>`;
    renderSettings();
  } catch (e) { toast(e.message, 'error'); }
}
