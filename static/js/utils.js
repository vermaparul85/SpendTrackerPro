// ── utils.js — helpers, toast, formatters ────────────────────────────────

function formatINR(amount) {
  if (amount == null) return '₹0.00';
  const num = typeof amount === 'number' ? amount : parseFloat(amount);
  if (isNaN(num)) return '₹0.00';
  const neg = num < 0;
  const absNum = Math.abs(num);
  const [int, dec] = absNum.toFixed(2).split('.');
  let r = [], s = int;
  if (s.length > 3) {
    r.push(s.slice(-3)); s = s.slice(0, -3);
    while (s.length > 2) { r.push(s.slice(-2)); s = s.slice(0, -2); }
    if (s) r.push(s);
    s = r.reverse().join(',');
  }
  return (neg ? '-' : '') + '₹' + (r.length ? s : int) + '.' + dec;
}

function formatLakhs(amount) {
  if (amount == null) return '₹0.00';
  const num = typeof amount === 'number' ? amount : parseFloat(amount);
  if (isNaN(num)) return '₹0.00';
  if (num >= 1e7) return `₹${(num / 1e7).toFixed(2)} Cr`;
  if (num >= 1e5) return `₹${(num / 1e5).toFixed(2)} L`;
  return formatINR(num);
}

function toast(message, type = 'info') {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = message;
  const container = document.getElementById('toast-container');
  if (container) {
    container.appendChild(el);
    setTimeout(() => el.remove(), 3200);
  }
}

function animateNumber(el, target, duration = 800, prefix = '', suffix = '') {
  if (!el) return;
  const num = typeof target === 'number' ? target : parseFloat(target);
  if (isNaN(num) || num <= 0) {
    el.textContent = prefix + formatINR(num || 0) + suffix;
    return;
  }
  const start = 0;
  const startTime = performance.now();
  const step = (now) => {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const val = start + (num - start) * eased;
    el.textContent = prefix + formatINR(val) + suffix;
    if (progress < 1) {
      requestAnimationFrame(step);
    } else {
      el.textContent = prefix + formatINR(num) + suffix;
    }
  };
  requestAnimationFrame(step);
}

function skeletonCard(height = 80) {
  return `<div class="skeleton" style="height:${height}px;border-radius:14px;"></div>`;
}

function markdownToHtml(md) {
  if (!md) return '';
  if (typeof marked !== 'undefined') return marked.parse(md);
  return md.replace(/\n/g, '<br>');
}

function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function getCategoryBadge(name) {
  if (!name) return 'badge-gray';
  const map = {
    'Groceries': 'badge-green', 'Dining': 'badge-amber', 'Shopping': 'badge-blue',
    'Utilities': 'badge-purple', 'Fuel': 'badge-amber', 'Travel': 'badge-blue',
    'Entertainment': 'badge-rose', 'Healthcare': 'badge-green',
    'Financials': 'badge-purple', 'Uncategorized': 'badge-gray',
  };
  const key = Object.keys(map).find(k => name.includes(k));
  return map[key] || 'badge-gray';
}
