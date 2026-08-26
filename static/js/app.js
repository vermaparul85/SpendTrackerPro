// ── app.js — SPA router and sidebar management ───────────────────────────

const PAGES = {
  dashboard: renderDashboard,
  insights:  renderInsights,
  ledger:    renderLedger,
  upload:    renderUpload,
  members:   renderMembers,
  rules:     renderRules,
  ai:        renderAIChat,
  settings:  renderSettings,
};

let _currentPage = null;

function navigate(page) {
  if (!PAGES[page]) page = 'dashboard';
  if (_currentPage === page) return;
  _currentPage = page;

  // Update nav active state
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.page === page);
  });

  // Update hash
  window.location.hash = page;

  // Destroy any existing Chart.js instances
  if (typeof destroyCharts === 'function') destroyCharts();

  // Render page
  PAGES[page]();
}

// Handle sidebar nav clicks
document.querySelectorAll('.nav-item').forEach(el => {
  el.addEventListener('click', e => {
    e.preventDefault();
    navigate(el.dataset.page);
  });
});

// Hash-based routing
function routeFromHash() {
  const hash = window.location.hash.replace('#', '') || 'dashboard';
  navigate(hash);
}

window.addEventListener('hashchange', routeFromHash);

// Initial load
(async () => {
  // Load settings to update sidebar status pills
  try {
    const s = await API.get('/api/settings');
    const pill = document.getElementById('api-pill');
    if (pill) {
      pill.style.display = 'none';
      pill.textContent = '';
    }
    if (s.db_mode === 'bigquery') {
      const pill = document.getElementById('db-pill');
      if (pill) { pill.className = 'status-pill pill-purple'; pill.textContent = '☁️ BigQuery Mode'; }
    }
  } catch {}

  routeFromHash();
})();
