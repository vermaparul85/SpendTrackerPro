// ── ai-chat.js ────────────────────────────────────────────────────────────
let _chatSession = null;
let _chatHistory = [];
let _chatApiKey = '';

function genSessionId() {
  return 'sess_' + Math.random().toString(36).slice(2);
}

async function renderAIChat() {
  _chatSession = _chatSession || genSessionId();
  // Load API key from settings
  try {
    const s = await API.get('/api/settings');
    _chatApiKey = s.api_key || '';
  } catch {}

  const root = document.getElementById('page-root');
  root.innerHTML = `
    <div class="page-header fade-in">
      <h2>🤖 AI Financial Assistant</h2>
      <p>Chat with your spending data — powered by Google ADK + Gemini</p>
    </div>
    <div class="page-content fade-in" style="display:flex;flex-direction:column;height:calc(100vh - 160px)">
      <div style="display:flex;gap:10px;align-items:center;margin-bottom:12px">
        <span class="status-pill pill-blue">🧠 gemini-2.0-flash</span>
        ${_chatApiKey ? '<span class="status-pill pill-green">🔑 API Key Active</span>' : '<span class="status-pill pill-amber">⚠️ No API Key</span>'}
        <button class="btn btn-secondary btn-sm" style="margin-left:auto" onclick="clearChat()">🗑️ Clear Chat</button>
      </div>
      ${!_chatApiKey ? `
        <div style="padding:16px;background:rgba(255,186,59,0.08);border:1px solid rgba(255,186,59,0.2);border-radius:10px;margin-bottom:16px;font-size:.875rem">
          ⚠️ <strong>No API key set.</strong> Go to <a href="#settings" style="color:var(--blue)" onclick="navigate('settings')">Settings</a> to add your Gemini API key and unlock the AI assistant.
        </div>` : ''}
      <div class="quick-chips" id="quick-chips">
        ${[
          ['📊 Spending Summary', 'Give me a spending summary for the last 3 months.'],
          ['🏆 Top Merchants', 'Who are my top 5 merchants by spend?'],
          ['⚠️ Large Purchases', 'Show high-value transactions above ₹10,000.'],
          ['📈 Full Insight Report', 'Generate a complete financial insights report.'],
          ['💡 Savings Tips', 'Give me personalised savings tips based on my spending.'],
        ].map(([label, msg]) => `<span class="chip" onclick="sendQuick('${msg.replace(/'/g, "\\'")}')">${label}</span>`).join('')}
      </div>
      <div class="chat-messages" id="chat-messages">
        <div class="chat-bubble" style="max-width:100%">
          <div class="bubble-avatar ai">🤖</div>
          <div class="bubble-content">
            <strong>Hello! I'm SpendTracker Pro AI.</strong><br>
            I have access to your complete transaction history and can help you understand your spending, categorize transactions, spot trends, and generate financial insights.<br><br>
            What would you like to know about your finances today?
          </div>
        </div>
      </div>
      <div class="chat-input-wrap">
        <textarea class="chat-input" id="chat-input" rows="1" placeholder="Ask about your spending..." onkeydown="handleChatKey(event)"></textarea>
        <button class="btn btn-primary" id="btn-send" onclick="sendChatMessage()" style="height:48px">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22,2 15,22 11,13 2,9"/></svg>
        </button>
      </div>
    </div>`;

  // Restore history
  _chatHistory.forEach(h => appendBubble(h.role, h.content, false));
  scrollChat();
}

function handleChatKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMessage(); }
}

function sendQuick(msg) {
  const input = document.getElementById('chat-input');
  if (input) { input.value = msg; sendChatMessage(); }
}

function clearChat() {
  _chatHistory = [];
  _chatSession = genSessionId();
  const msgs = document.getElementById('chat-messages');
  if (msgs) {
    msgs.innerHTML = `<div class="chat-bubble"><div class="bubble-avatar ai">🤖</div>
      <div class="bubble-content">Chat cleared. How can I help you?</div></div>`;
  }
}

function scrollChat() {
  const el = document.getElementById('chat-messages');
  if (el) el.scrollTop = el.scrollHeight;
}

function appendBubble(role, content, animate = true) {
  const msgs = document.getElementById('chat-messages');
  if (!msgs) return null;
  const div = document.createElement('div');
  div.className = `chat-bubble ${role === 'user' ? 'user' : ''}${animate ? ' slide-up' : ''}`;
  div.innerHTML = `
    <div class="bubble-avatar ${role === 'user' ? 'user' : 'ai'}">${role === 'user' ? '👤' : '🤖'}</div>
    <div class="bubble-content"></div>`;
  msgs.appendChild(div);
  scrollChat();
  return div.querySelector('.bubble-content');
}

async function sendChatMessage() {
  const input = document.getElementById('chat-input');
  const message = input?.value.trim();
  if (!message) return;
  if (!_chatApiKey) { toast('Please set your Gemini API key in Settings first.', 'warning'); return; }

  input.value = '';
  input.style.height = 'auto';

  appendBubble('user', message);
  _chatHistory.push({ role: 'user', content: message });
  scrollChat();

  const btn = document.getElementById('btn-send');
  if (btn) btn.disabled = true;

  // Typing indicator
  const typingEl = appendBubble('assistant', '');
  if (typingEl) typingEl.innerHTML = `<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>`;

  let fullResponse = '';

  API.streamChat(
    { message, session_id: _chatSession, api_key: _chatApiKey },
    chunk => {
      fullResponse += chunk;
      if (typingEl) typingEl.innerHTML = markdownToHtml(fullResponse);
      scrollChat();
    },
    () => {
      if (typingEl && !fullResponse) typingEl.innerHTML = 'I couldn\'t generate a response. Please try again.';
      if (fullResponse) _chatHistory.push({ role: 'assistant', content: fullResponse });
      if (btn) btn.disabled = false;
      scrollChat();
    },
    err => {
      if (typingEl) typingEl.innerHTML = `<span style="color:var(--rose)">⚠️ Error: ${err}</span>`;
      if (btn) btn.disabled = false;
      toast(String(err), 'error');
    }
  );
}
