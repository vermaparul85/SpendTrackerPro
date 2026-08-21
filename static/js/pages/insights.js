// ── insights.js ───────────────────────────────────────────────────────────
async function renderInsights() {
  const root = document.getElementById('page-root');
  root.innerHTML = `
    <div class="page-header fade-in">
      <h2>⚡ Financial Insights</h2>
      <p>AI-powered analysis of your household spending patterns</p>
    </div>
    <div class="page-content fade-in">
      <div class="card">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
          <div class="card-title" style="margin-bottom:0">Insight Report</div>
          <div style="display:flex;gap:8px">
            <button class="btn btn-secondary btn-sm" onclick="copyInsights()">📋 Copy</button>
            <button class="btn btn-primary btn-sm" onclick="refreshInsights()">🔄 Regenerate</button>
          </div>
        </div>
        <div id="insight-body">
          <div style="display:flex;align-items:center;gap:10px;padding:24px;color:var(--text-2)">
            <div class="skeleton" style="width:100%;height:400px;border-radius:10px;"></div>
          </div>
        </div>
      </div>
    </div>`;
  loadInsights();
}

let _insightText = '';

async function loadInsights() {
  const el = document.getElementById('insight-body');
  try {
    const data = await API.get('/api/insights');
    _insightText = data.report || '';
    el.innerHTML = `<div class="insight-report">${markdownToHtml(_insightText)}</div>`;
  } catch (e) {
    el.innerHTML = `<div style="color:var(--rose);padding:16px">⚠️ ${e.message}</div>`;
    toast('Failed to load insights: ' + e.message, 'error');
  }
}

async function refreshInsights() {
  const el = document.getElementById('insight-body');
  el.innerHTML = '<div class="skeleton" style="height:400px;border-radius:10px;"></div>';
  await loadInsights();
}

function copyInsights() {
  if (_insightText) {
    navigator.clipboard.writeText(_insightText).then(() => toast('Report copied to clipboard!', 'success'));
  }
}
