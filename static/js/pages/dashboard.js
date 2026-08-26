// ── dashboard.js ─────────────────────────────────────────────────────────
let _charts = {};
let _activeTimeframe = 'all'; // 'all' | '90d' | '30d' | 'year' | 'custom'
let _trendViewMode = 'total'; // 'member' | 'total'
let _trendData = null;
let _categoryData = null;
let _highValueData = [];
let _customStartDate = '';
let _customEndDate = '';

function destroyCharts() {
  Object.values(_charts).forEach(c => c && typeof c.destroy === 'function' && c.destroy());
  _charts = {};
}

const CHART_DEFAULTS = {
  color: '#8B9DC3',
  borderColor: 'rgba(255,255,255,0.07)',
  grid: { color: 'rgba(255,255,255,0.05)', borderColor: 'transparent' },
  plugins: { legend: { labels: { color: '#8B9DC3', font: { family: 'Inter', size: 12 } } } },
};

function computePresetDates(tf) {
  if (tf === 'all') return { start_date: '', end_date: '' };
  const today = new Date();
  const endStr = today.toISOString().split('T')[0];
  let start = new Date();
  if (tf === '30d') {
    start.setDate(today.getDate() - 30);
  } else if (tf === '90d') {
    start.setDate(today.getDate() - 90);
  } else if (tf === 'year') {
    start = new Date(today.getFullYear(), 0, 1);
  }
  const startStr = start.toISOString().split('T')[0];
  return { start_date: startStr, end_date: endStr };
}

async function renderDashboard() {
  const root = document.getElementById('page-root');
  root.innerHTML = `
    <div class="page-header fade-in">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px">
        <div>
          <h2>📊 Dashboard</h2>
          <p id="dashboard-subtitle">Consolidated household financial intelligence & spend overview</p>
        </div>

        <!-- Filter Controls: Presets + Custom Date Range -->
        <div style="display:flex;align-items:center;flex-wrap:wrap;gap:10px">
          <!-- Timeframe Preset Buttons -->
          <div style="display:flex;gap:4px;background:rgba(255,255,255,0.04);padding:4px;border-radius:10px;border:1px solid var(--border)">
            <button id="btn-tf-all" class="btn btn-sm ${(_activeTimeframe === 'all' ? 'btn-primary' : 'btn-secondary')}" style="padding:5px 12px;font-size:.78rem" onclick="switchDashboardTimeframe('all')">All Time</button>
            <button id="btn-tf-90d" class="btn btn-sm ${(_activeTimeframe === '90d' ? 'btn-primary' : 'btn-secondary')}" style="padding:5px 12px;font-size:.78rem" onclick="switchDashboardTimeframe('90d')">90 Days</button>
            <button id="btn-tf-30d" class="btn btn-sm ${(_activeTimeframe === '30d' ? 'btn-primary' : 'btn-secondary')}" style="padding:5px 12px;font-size:.78rem" onclick="switchDashboardTimeframe('30d')">30 Days</button>
            <button id="btn-tf-year" class="btn btn-sm ${(_activeTimeframe === 'year' ? 'btn-primary' : 'btn-secondary')}" style="padding:5px 12px;font-size:.78rem" onclick="switchDashboardTimeframe('year')">This Year</button>
          </div>

          <!-- Custom Start & End Date Inputs -->
          <div style="display:flex;align-items:center;gap:6px;background:rgba(255,255,255,0.03);padding:4px 8px;border-radius:10px;border:1px solid var(--border)">
            <div style="display:flex;align-items:center;gap:4px">
              <label for="dash-start" style="font-size:.72rem;color:var(--text-3);margin-bottom:0;text-transform:uppercase;font-weight:600">From</label>
              <input type="date" id="dash-start" value="${_customStartDate}" style="padding:4px 8px;font-size:.78rem;width:130px;background:rgba(255,255,255,0.05);border:1px solid var(--border);border-radius:6px;color:var(--text-1)" onchange="onDateInputChange()" />
            </div>
            <div style="display:flex;align-items:center;gap:4px">
              <label for="dash-end" style="font-size:.72rem;color:var(--text-3);margin-bottom:0;text-transform:uppercase;font-weight:600">To</label>
              <input type="date" id="dash-end" value="${_customEndDate}" style="padding:4px 8px;font-size:.78rem;width:130px;background:rgba(255,255,255,0.05);border:1px solid var(--border);border-radius:6px;color:var(--text-1)" onchange="onDateInputChange()" />
            </div>
            <button class="btn btn-primary btn-sm" style="padding:4px 10px;font-size:.75rem" onclick="applyCustomDashboardDates()">Filter</button>
            ${(_activeTimeframe !== 'all' || _customStartDate || _customEndDate ? '<button class="btn btn-secondary btn-sm" style="padding:4px 8px;font-size:.75rem" onclick="resetDashboardDates()" title="Reset to All Time">✕</button>' : '')}
          </div>
        </div>
      </div>
    </div>

    <div class="page-content fade-in">
      <div class="kpi-grid" id="kpi-grid">
        ${[1, 2, 3, 4, 5].map(() => skeletonCard(90)).join('')}
      </div>
      <div class="grid-6040">
        <div class="card">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:12px">
            <div class="card-title" style="margin-bottom:0">Monthly Spend Trend</div>
            <div style="display:flex;gap:3px;background:rgba(255,255,255,0.04);padding:3px;border-radius:8px;border:1px solid var(--border)">
              <button id="btn-trend-total" class="btn btn-sm ${(_trendViewMode === 'total' ? 'btn-primary' : 'btn-secondary')}" style="padding:3px 10px;font-size:.72rem" onclick="switchTrendViewMode('total')">📊 Total & Credits</button>
              <button id="btn-trend-member" class="btn btn-sm ${(_trendViewMode === 'member' ? 'btn-primary' : 'btn-secondary')}" style="padding:3px 10px;font-size:.72rem" onclick="switchTrendViewMode('member')">👥 By Family Member</button>
            </div>
          </div>
          <div class="chart-wrap" id="wrap-trend"><canvas id="chart-trend"></canvas></div>
        </div>
        <div class="card">
          <div class="card-title">Spending Share by Family Members</div>
          <div class="chart-wrap" id="wrap-member-share"><canvas id="chart-member-share"></canvas></div>
        </div>
      </div>
      <div class="card" style="margin-top:16px; margin-bottom:20px">
        <div class="card-title">Spending by Category per Month</div>
        <div class="chart-wrap" id="wrap-category-monthly"><canvas id="chart-category-monthly"></canvas></div>
      </div>
      <div class="grid-2">
        <div class="card">
          <div class="card-title">Spending by Category</div>
          <div class="chart-wrap" id="wrap-cat"><canvas id="chart-cat"></canvas></div>
        </div>
        <div class="card">
          <div class="card-title">Spending by Bank</div>
          <div class="chart-wrap" id="wrap-bank-share"><canvas id="chart-bank-share"></canvas></div>
        </div>
      </div>
      <div class="grid-2">
        <div class="card">
          <div class="card-title">Top Merchants</div>
          <div class="merchant-bar" id="merchant-bar"><div class="skeleton" style="height:160px;border-radius:8px;"></div></div>
        </div>
        <div class="card">
          <div class="card-title">Recent Transactions</div>
          <div class="table-wrap" id="recent-tx"><div class="skeleton" style="height:200px;border-radius:8px;"></div></div>
        </div>
      </div>
    </div>`;

  await loadDashboardData();
}

function updatePresetButtonStyles() {
  ['all', '90d', '30d', 'year'].forEach(tf => {
    const btn = document.getElementById(`btn-tf-${tf}`);
    if (btn) {
      if (_activeTimeframe === tf) {
        btn.className = 'btn btn-sm btn-primary';
      } else {
        btn.className = 'btn btn-sm btn-secondary';
      }
    }
  });
}

function onDateInputChange() {
  const startVal = document.getElementById('dash-start')?.value || '';
  const endVal = document.getElementById('dash-end')?.value || '';
  if (startVal || endVal) {
    _activeTimeframe = 'custom';
    updatePresetButtonStyles();
  }
}

async function switchDashboardTimeframe(tf) {
  _activeTimeframe = tf;
  if (tf === 'all') {
    _customStartDate = '';
    _customEndDate = '';
  } else {
    const dates = computePresetDates(tf);
    _customStartDate = dates.start_date;
    _customEndDate = dates.end_date;
  }

  const startInput = document.getElementById('dash-start');
  const endInput = document.getElementById('dash-end');
  if (startInput) startInput.value = _customStartDate;
  if (endInput) endInput.value = _customEndDate;

  updatePresetButtonStyles();
  await loadDashboardData();
}

async function applyCustomDashboardDates() {
  const startVal = document.getElementById('dash-start')?.value || '';
  const endVal = document.getElementById('dash-end')?.value || '';

  if (startVal && endVal && startVal > endVal) {
    toast('Start date cannot be after end date', 'warning');
    return;
  }

  _customStartDate = startVal;
  _customEndDate = endVal;

  if (!_customStartDate && !_customEndDate) {
    _activeTimeframe = 'all';
  } else {
    _activeTimeframe = 'custom';
  }

  updatePresetButtonStyles();
  await loadDashboardData();
}

async function resetDashboardDates() {
  _activeTimeframe = 'all';
  _customStartDate = '';
  _customEndDate = '';

  const startInput = document.getElementById('dash-start');
  const endInput = document.getElementById('dash-end');
  if (startInput) startInput.value = '';
  if (endInput) endInput.value = '';

  updatePresetButtonStyles();
  await loadDashboardData();
}

async function loadDashboardData() {
  destroyCharts();

  let params = {};
  if (_activeTimeframe === 'custom') {
    if (_customStartDate) params.start_date = _customStartDate;
    if (_customEndDate) params.end_date = _customEndDate;
  } else if (_activeTimeframe !== 'all') {
    const dates = computePresetDates(_activeTimeframe);
    if (dates.start_date) params.start_date = dates.start_date;
    if (dates.end_date) params.end_date = dates.end_date;
  }

  const qStr = new URLSearchParams(params).toString();

  try {
    const [summary, charts] = await Promise.all([
      API.get(`/api/dashboard/summary?${qStr}`),
      API.get(`/api/dashboard/charts?${qStr}`)
    ]);

    // Update dynamic subtitle with active range & count
    const subEl = document.getElementById('dashboard-subtitle');
    if (subEl) {
      if (summary.date_range?.start && summary.date_range?.end) {
        subEl.textContent = `Showing ${summary.metrics.tx_count} transactions (${summary.date_range.start} to ${summary.date_range.end})`;
      } else if (summary.metrics.tx_count > 0) {
        subEl.textContent = `Showing all ${summary.metrics.tx_count} transactions in ledger`;
      } else {
        subEl.textContent = `Consolidated household financial intelligence & spend overview`;
      }
    }

    _highValueData = charts.high_value || [];
    _categoryData = charts.category_donut || { labels: [], data: [], members: [] };
    renderKPIs(summary.metrics, summary.members);
    renderTrendChart(charts.monthly_trend);
    renderMemberShareChart(charts.member_share_donut);
    renderCategoryMonthlyChart(charts.category_monthly_line);
    renderCatChart(_categoryData);
    renderBankShareChart(charts.bank_share_donut);
    renderMerchants(summary.top_merchants);
    renderRecentTx(summary.recent_transactions);
  } catch (e) {
    toast('Failed to load dashboard: ' + e.message, 'error');
  }
}

function renderKPIs(m, members) {
  const kpiEl = document.getElementById('kpi-grid');
  if (!kpiEl) return;

  kpiEl.innerHTML = `
    <div class="kpi-card" style="--kpi-color:#4F8EFF">
      <div class="kpi-icon">💸</div>
      <div class="kpi-label">Total Spend</div>
      <div class="kpi-value" id="kpi-spend">${m.total_spend_fmt || '₹0.00'}</div>
      <div class="kpi-sub">Debits & Expenses</div>
    </div>
    <div class="kpi-card" style="--kpi-color:#00D18C">
      <div class="kpi-icon">💳</div>
      <div class="kpi-label">Total Credits &amp; Refunds</div>
      <div class="kpi-value">${m.total_credit_fmt || '₹0.00'}</div>
      <div class="kpi-sub">Credits, refunds & payments</div>
    </div>
    <div class="kpi-card" style="--kpi-color:#FFBA3B">
      <div class="kpi-icon">🏆</div>
      <div class="kpi-label">Top Category</div>
      <div class="kpi-value" style="font-size:1.1rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escapeHtml(m.top_category)}">${escapeHtml(m.top_category)}</div>
      <div class="kpi-sub">${m.top_category_amt_fmt}</div>
    </div>
    <div class="kpi-card" style="--kpi-color:#A78BFA">
      <div class="kpi-icon">📈</div>
      <div class="kpi-label">Transactions</div>
      <div class="kpi-value">${m.tx_count}</div>
      <div class="kpi-sub">${m.bank_count} bank${m.bank_count !== 1 ? 's' : ''} tracked</div>
    </div>
    <div class="kpi-card" style="--kpi-color:#FF5B7F;cursor:pointer;position:relative" onclick="showHighValueModal()" title="Click to view high-value transactions">
      <div class="kpi-icon">🚨</div>
      <div class="kpi-label">High-Value (≥₹10k)</div>
      <div class="kpi-value">${m.high_val_count}</div>
      <div class="kpi-sub">Large purchases · <span style="color:#FF5B7F;font-weight:600">Click to view</span></div>
      <div style="position:absolute;top:8px;right:10px;font-size:.65rem;color:rgba(255,91,127,0.6);font-weight:700;letter-spacing:.05em">↗</div>
    </div>`;

  const spendEl = document.getElementById('kpi-spend');
  if (spendEl && m.total_spend > 0) {
    animateNumber(spendEl, m.total_spend);
  }
}

function showHighValueModal() {
  // Remove any existing modal
  const existing = document.getElementById('hv-modal-overlay');
  if (existing) existing.remove();

  const rows = _highValueData.length === 0
    ? `<tr><td colspan="5" style="text-align:center;padding:32px;color:var(--text-3)">No high-value transactions (≥₹10,000) in the current period.</td></tr>`
    : _highValueData.map((tx, i) => `
      <tr style="border-bottom:1px solid var(--border);transition:background .15s" onmouseover="this.style.background='rgba(255,91,127,0.06)'" onmouseout="this.style.background='transparent'">
        <td style="padding:10px 14px;font-size:.8rem;color:var(--text-3);white-space:nowrap">${escapeHtml(tx.transaction_date)}</td>
        <td style="padding:10px 14px;font-weight:600;color:var(--text-1)">${escapeHtml(tx.clean_merchant)}</td>
        <td style="padding:10px 14px;font-size:.82rem;color:var(--text-2)">${escapeHtml(tx.category_name)}</td>
        <td style="padding:10px 14px;font-size:.8rem;color:var(--text-3)">${escapeHtml(tx.member_name)}</td>
        <td style="padding:10px 14px;text-align:right;font-weight:700;color:#FF5B7F;font-family:var(--mono);white-space:nowrap">${escapeHtml(tx.amount_fmt)}</td>
      </tr>`).join('');

  const total = _highValueData.reduce((s, t) => s + t.amount, 0);
  const totalFmt = formatINR(total);

  const overlay = document.createElement('div');
  overlay.id = 'hv-modal-overlay';
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(5,8,20,0.82);backdrop-filter:blur(6px);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px';
  overlay.innerHTML = `
    <div style="background:var(--bg-1);border:1px solid rgba(255,91,127,0.25);border-radius:16px;width:100%;max-width:820px;max-height:88vh;display:flex;flex-direction:column;box-shadow:0 24px 80px rgba(0,0,0,0.5)" onclick="event.stopPropagation()">
      <div style="display:flex;align-items:center;justify-content:space-between;padding:20px 24px;border-bottom:1px solid var(--border);flex-shrink:0">
        <div>
          <div style="font-size:1.05rem;font-weight:700;color:var(--text-1);display:flex;align-items:center;gap:8px">🚨 High-Value Transactions <span style="font-size:.75rem;color:var(--text-3);font-weight:400">(≥ ₹10,000)</span></div>
          <div style="font-size:.78rem;color:var(--text-3);margin-top:3px">${_highValueData.length} transaction${_highValueData.length !== 1 ? 's' : ''} · Total: <span style="color:#FF5B7F;font-weight:700">${totalFmt}</span></div>
        </div>
        <button onclick="document.getElementById('hv-modal-overlay').remove()" style="background:rgba(255,255,255,0.07);border:1px solid var(--border);color:var(--text-2);border-radius:8px;padding:6px 12px;cursor:pointer;font-size:.85rem;transition:all .15s" onmouseover="this.style.background='rgba(255,255,255,0.12)'" onmouseout="this.style.background='rgba(255,255,255,0.07)'">✕ Close</button>
      </div>
      <div style="overflow-y:auto;flex:1">
        <table style="width:100%;border-collapse:collapse">
          <thead style="position:sticky;top:0;background:var(--bg-2);z-index:1">
            <tr>
              <th style="padding:10px 14px;text-align:left;font-size:.72rem;font-weight:700;color:var(--text-3);text-transform:uppercase;letter-spacing:.06em;white-space:nowrap">Date</th>
              <th style="padding:10px 14px;text-align:left;font-size:.72rem;font-weight:700;color:var(--text-3);text-transform:uppercase;letter-spacing:.06em">Merchant</th>
              <th style="padding:10px 14px;text-align:left;font-size:.72rem;font-weight:700;color:var(--text-3);text-transform:uppercase;letter-spacing:.06em">Category</th>
              <th style="padding:10px 14px;text-align:left;font-size:.72rem;font-weight:700;color:var(--text-3);text-transform:uppercase;letter-spacing:.06em">Member</th>
              <th style="padding:10px 14px;text-align:right;font-size:.72rem;font-weight:700;color:var(--text-3);text-transform:uppercase;letter-spacing:.06em">Amount</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      <div style="padding:14px 24px;border-top:1px solid var(--border);display:flex;justify-content:flex-end;gap:8px;flex-shrink:0">
        <div style="flex:1;display:flex;align-items:center;gap:6px;font-size:.8rem;color:var(--text-3)">💡 Showing up to 20 most recent high-value transactions in the selected timeframe</div>
        <button onclick="document.getElementById('hv-modal-overlay').remove()" style="background:rgba(255,91,127,0.12);border:1px solid rgba(255,91,127,0.3);color:#FF5B7F;border-radius:8px;padding:7px 18px;cursor:pointer;font-size:.82rem;font-weight:600;transition:all .15s" onmouseover="this.style.background='rgba(255,91,127,0.2)'" onmouseout="this.style.background='rgba(255,91,127,0.12)'">Close</button>
      </div>
    </div>`;

  overlay.addEventListener('click', () => overlay.remove());
  document.body.appendChild(overlay);

  // Close on Escape key
  const onKey = e => { if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', onKey); } };
  document.addEventListener('keydown', onKey);
}

function renderTrendChart(data) {
  _trendData = data;
  const wrap = document.getElementById('wrap-trend');
  if (!wrap) return;

  if (_charts.trend) {
    _charts.trend.destroy();
    _charts.trend = null;
  }

  if (!data || !data.labels || data.labels.length === 0) {
    wrap.innerHTML = `<div class="empty-state" style="padding:40px 10px"><div class="empty-icon">📈</div><p>No monthly spend data yet.<br><span style="font-size:.78rem;color:var(--text-3)">Upload a statement to visualize monthly trends.</span></p></div>`;
    return;
  }

  wrap.innerHTML = `<canvas id="chart-trend"></canvas>`;
  const ctx = document.getElementById('chart-trend');
  if (!ctx) return;

  let datasets = [];
  let isStacked = false;

  if (_trendViewMode === 'member' && data.members && data.members.length > 0) {
    isStacked = true;
    const lastIdx = data.members.length - 1;
    datasets = data.members.map((m, idx) => ({
      label: `👤 ${m.member_name}`,
      data: m.data,
      backgroundColor: m.color || '#4F8EFF',
      // Only round the very top of the topmost (last) stacked segment.
      // Middle and bottom segments must be perfectly flat on all corners.
      borderRadius: idx === lastIdx
        ? { topLeft: 5, topRight: 5, bottomLeft: 0, bottomRight: 0 }
        : { topLeft: 0, topRight: 0, bottomLeft: 0, bottomRight: 0 },
      // borderSkipped must be 'bottom' for all so Chart.js skips bottom edge —
      // this prevents the base bar from showing a cap at its bottom border.
      borderSkipped: 'bottom',
      stack: 'members',
    }));
  } else {
    isStacked = false;
    datasets = [
      {
        label: '💸 Spend (Debits)',
        data: data.debit,
        backgroundColor: 'rgba(79,142,255,0.8)',
        borderRadius: { topLeft: 5, topRight: 5, bottomLeft: 0, bottomRight: 0 },
        borderSkipped: 'bottom',
      },
      {
        label: '💳 Credits & Refunds',
        data: data.credit,
        backgroundColor: 'rgba(0,209,140,0.6)',
        borderRadius: { topLeft: 5, topRight: 5, bottomLeft: 0, bottomRight: 0 },
        borderSkipped: 'bottom',
      },
    ];
  }

  _charts.trend = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        ...CHART_DEFAULTS.plugins,
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.dataset.label}: ${formatINR(ctx.parsed.y)}`,
            footer: tooltipItems => {
              if (isStacked && tooltipItems.length > 0) {
                const index = tooltipItems[0]?.dataIndex ?? 0;
                const totalMonth = Array.isArray(data.debit) ? (Number(data.debit[index]) || 0) : 0;
                return `Total Month Spend: ${formatINR(totalMonth)}`;
              }
              return '';
            }
          }
        }
      },
      scales: {
        x: {
          stacked: isStacked,
          ticks: { color: '#8B9DC3', font: { family: 'Inter', size: 11 } },
          grid: CHART_DEFAULTS.grid
        },
        y: {
          stacked: isStacked,
          ticks: { color: '#8B9DC3', callback: v => formatLakhs(v), font: { family: 'Inter', size: 11 } },
          grid: CHART_DEFAULTS.grid
        },
      }
    }
  });
}

function switchTrendViewMode(mode) {
  _trendViewMode = mode;
  const btnMember = document.getElementById('btn-trend-member');
  const btnTotal = document.getElementById('btn-trend-total');
  if (btnMember && btnTotal) {
    btnMember.className = mode === 'member' ? 'btn btn-sm btn-primary' : 'btn btn-sm btn-secondary';
    btnTotal.className = mode === 'total' ? 'btn btn-sm btn-primary' : 'btn btn-sm btn-secondary';
  }
  if (_trendData) {
    renderTrendChart(_trendData);
  }
}

function renderMemberShareChart(data) {
  const wrap = document.getElementById('wrap-member-share');
  if (!wrap) return;

  if (!data || !data.labels || data.labels.length === 0 || data.data.every(v => v === 0)) {
    wrap.innerHTML = `<div class="empty-state" style="padding:40px 10px"><div class="empty-icon">👨‍👩‍👧‍👦</div><p>No family spending split available.<br><span style="font-size:.78rem;color:var(--text-3)">Member spend will appear once transactions are recorded.</span></p></div>`;
    return;
  }

  wrap.innerHTML = `<canvas id="chart-member-share"></canvas>`;
  const ctx = document.getElementById('chart-member-share');
  if (!ctx) return;

  const softerPalette = [
    '#4F8EFF', '#00D18C', '#FFBA3B', '#FF7A90', '#9B8CFF',
    '#5EC8FF', '#F59E0B', '#4ADE80', '#F472B6', '#94A3B8'
  ];

  _charts.memberShare = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.labels,
      datasets: [{
        data: data.data,
        backgroundColor: data.colors?.length ? data.colors : softerPalette,
        borderColor: '#101827',
        borderWidth: 2,
        hoverOffset: 10,
        spacing: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '58%',
      layout: { padding: 12 },
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: {
          position: 'bottom',
          align: 'center',
          labels: {
            color: '#C9D1E6',
            boxWidth: 12,
            boxHeight: 12,
            padding: 14,
            usePointStyle: true,
            pointStyle: 'circle',
            font: { family: 'Inter', size: 11 }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.92)',
          titleColor: '#F8FAFC',
          bodyColor: '#E2E8F0',
          padding: 10,
          displayColors: true,
          callbacks: {
            label: ctx => {
              const total = ctx.dataset.data.reduce((sum, value) => sum + Number(value || 0), 0);
              const val = Number(ctx.parsed || 0);
              const pct = total > 0 ? ((val / total) * 100).toFixed(1) : '0.0';
              return ` ${ctx.label}: ${formatINR(val)} (${pct}%)`;
            }
          }
        }
      }
    }
  });
}

function renderCategoryMonthlyChart(data) {
  const wrap = document.getElementById('wrap-category-monthly');
  if (!wrap) return;

  if (!data || !data.labels || data.labels.length === 0 || !data.datasets || data.datasets.length === 0) {
    wrap.innerHTML = `<div class="empty-state" style="padding:40px 10px"><div class="empty-icon">📈</div><p>No monthly category trend available.<br><span style="font-size:.78rem;color:var(--text-3)">Category spending trend will appear once transactions are recorded.</span></p></div>`;
    return;
  }

  wrap.innerHTML = `<canvas id="chart-category-monthly"></canvas>`;
  const ctx = document.getElementById('chart-category-monthly');
  if (!ctx) return;

  const palette = [
    '#4F8EFF', '#18C78C', '#FFB020', '#FF5C8A', '#8B6EF6',
    '#2EC5FF', '#FF8D3A', '#3EDB90', '#F96AC6', '#8AA3FF'
  ];

  _charts.categoryMonthly = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: data.datasets.map((dataset, idx) => {
        const color = dataset.borderColor || dataset.backgroundColor || palette[idx % palette.length];
        return {
          ...dataset,
          backgroundColor: color,
          borderColor: 'rgba(255,255,255,0.18)',
          borderWidth: 1,
          borderRadius: 8,
          maxBarThickness: 100,
          barPercentage: 1,
          categoryPercentage: 1,
          stack: 'monthly-category',
        };
      })
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: {
          position: 'bottom',
          align: 'center',
          labels: {
            color: '#C9D1E6',
            boxWidth: 12,
            boxHeight: 12,
            padding: 14,
            usePointStyle: true,
            pointStyle: 'circle',
            font: { family: 'Inter', size: 11 }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.92)',
          titleColor: '#F8FAFC',
          bodyColor: '#E2E8F0',
          padding: 10,
          callbacks: {
            label: tooltipItem => {
              const value = Number(tooltipItem.parsed.y || 0);
              return value > 0 ? ` ${tooltipItem.dataset.label}: ${formatINR(value)}` : '';
            },
            footer: tooltipItems => {
              if (!tooltipItems || tooltipItems.length === 0) return '';
              const total = tooltipItems.reduce((sum, item) => sum + Number(item.parsed.y || 0), 0);
              return `Total: ${formatINR(total)}`;
            }
          }
        }
      },
      scales: {
        x: {
          stacked: true,
          ticks: { color: '#8B9DC3', font: { family: 'Inter', size: 10 } },
          grid: CHART_DEFAULTS.grid
        },
        y: {
          stacked: true,
          beginAtZero: false,
          ticks: {
            color: '#8B9DC3',
            callback: value => formatLakhs(value),
            font: { family: 'Inter', size: 10 }
          },
          grid: CHART_DEFAULTS.grid
        }
      }
    }
  });
}

function renderCatChart(data) {
  const wrap = document.getElementById('wrap-cat');
  if (!wrap) return;

  if (!data || !data.labels || data.labels.length === 0 || data.data.every(v => v === 0)) {
    wrap.innerHTML = `<div class="empty-state" style="padding:40px 10px"><div class="empty-icon">🏷️</div><p>No category breakdown available.<br><span style="font-size:.78rem;color:var(--text-3)">Transactions will automatically map to spending categories.</span></p></div>`;
    return;
  }

  wrap.innerHTML = `<canvas id="chart-cat"></canvas>`;
  const ctx = document.getElementById('chart-cat');
  if (!ctx) return;

  _charts.cat = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Category Spend',
        data: data.data,
        backgroundColor: data.colors || ['#4F8EFF'],
        borderColor: 'rgba(255,255,255,0.12)',
        borderWidth: 1,
        borderRadius: 8,
        maxBarThickness: 28,
        barPercentage: 0.8,
        categoryPercentage: 0.9
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: chartCtx => ` ${chartCtx.label}: ${formatINR(chartCtx.parsed.x ?? chartCtx.parsed)}`
          }
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          grid: CHART_DEFAULTS.grid,
          ticks: {
            color: '#8B9DC3',
            callback: value => formatLakhs(value),
            font: { family: 'Inter', size: 10 }
          }
        },
        y: {
          grid: { display: false },
          ticks: {
            color: '#C9D1E6',
            font: { family: 'Inter', size: 11 }
          }
        }
      }
    }
  });
}

function renderBankShareChart(data) {
  const wrap = document.getElementById('wrap-bank-share');
  if (!wrap) return;

  if (!data || !data.labels || data.labels.length === 0 || data.data.every(v => v === 0)) {
    wrap.innerHTML = `<div class="empty-state" style="padding:40px 10px"><div class="empty-icon">🏦</div><p>No bank spend share available.<br><span style="font-size:.78rem;color:var(--text-3)">Bank spend will appear once transactions are recorded.</span></p></div>`;
    return;
  }

  wrap.innerHTML = `<canvas id="chart-bank-share"></canvas>`;
  const ctx = document.getElementById('chart-bank-share');
  if (!ctx) return;

  _charts.bankShare = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.labels,
      datasets: [{
        data: data.data,
        backgroundColor: data.colors || ['#4F8EFF', '#00D18C', '#FFBA3B', '#FF5B7F', '#A78BFA'],
        borderColor: '#101827',
        borderWidth: 2,
        hoverOffset: 8,
        spacing: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '58%',
      layout: { padding: 12 },
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: {
          position: 'bottom',
          align: 'center',
          labels: {
            color: '#C9D1E6',
            boxWidth: 12,
            boxHeight: 12,
            padding: 14,
            usePointStyle: true,
            pointStyle: 'circle',
            font: { family: 'Inter', size: 11 }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.92)',
          titleColor: '#F8FAFC',
          bodyColor: '#E2E8F0',
          padding: 10,
          displayColors: true,
          callbacks: {
            label: chartCtx => {
              const total = chartCtx.dataset.data.reduce((sum, value) => sum + Number(value || 0), 0);
              const val = Number(chartCtx.parsed || 0);
              const pct = total > 0 ? ((val / total) * 100).toFixed(1) : '0.0';
              return ` ${chartCtx.label}: ${formatINR(val)} (${pct}%)`;
            }
          }
        }
      }
    }
  });
}

function renderMerchants(merchants) {
  const el = document.getElementById('merchant-bar');
  if (!el) return;
  if (!merchants || !merchants.length) {
    el.innerHTML = '<div class="empty-state" style="padding:30px 10px"><p>No merchant data yet</p></div>';
    return;
  }
  const max = merchants[0].amount || 1.0;
  el.innerHTML = merchants.map(m => `
    <div class="merchant-row">
      <span class="merchant-name" title="${escapeHtml(m.merchant)}">${escapeHtml(m.merchant)}</span>
      <div class="merchant-track"><div class="merchant-fill" style="width:${Math.min(100, (m.amount / max * 100)).toFixed(1)}%"></div></div>
      <span class="merchant-amt">${m.amount_fmt}</span>
    </div>`).join('');
}

function renderRecentTx(txs) {
  const el = document.getElementById('recent-tx');
  if (!el) return;
  if (!txs || !txs.length) {
    el.innerHTML = '<div class="empty-state" style="padding:30px 10px"><p>No transactions yet</p></div>';
    return;
  }
  el.innerHTML = `<table>
    <thead><tr><th>Date</th><th>Merchant</th><th>Amount</th><th>Type</th></tr></thead>
    <tbody>${txs.map(t => `
      <tr>
        <td style="color:var(--text-3);font-size:.8rem">${t.transaction_date}</td>
        <td><span class="badge ${getCategoryBadge(t.category_name)}">${t.category_icon}</span> ${escapeHtml(t.clean_merchant)}</td>
        <td class="${t.transaction_type === 'Debit' ? 'amount-debit' : 'amount-credit'}">${t.transaction_type === 'Debit' ? '-' : '+'} ${t.amount_fmt}</td>
        <td><span class="badge ${t.transaction_type === 'Debit' ? 'badge-rose' : 'badge-green'}">${t.transaction_type}</span></td>
      </tr>`).join('')}</tbody></table>`;
}
