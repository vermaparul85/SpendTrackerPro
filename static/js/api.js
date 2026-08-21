// ── api.js — fetch wrapper with error handling ───────────────────────────

const API = {
  async get(path) {
    const r = await fetch(path);
    if (!r.ok) throw new Error(`API ${path} failed: ${r.status}`);
    return r.json();
  },
  async post(path, body) {
    const r = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      throw new Error(err.error || `API ${path} failed: ${r.status}`);
    }
    return r.json();
  },
  async patch(path, body) {
    const r = await fetch(path, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`API ${path} failed: ${r.status}`);
    return r.json();
  },
  async delete(path) {
    const r = await fetch(path, { method: 'DELETE' });
    if (!r.ok) throw new Error(`API ${path} failed: ${r.status}`);
    return r.json();
  },
  async uploadForm(path, formData) {
    const r = await fetch(path, { method: 'POST', body: formData });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || `Upload failed: ${r.status}`);
    return data;
  },
  // SSE streaming for AI chat
  streamChat(body, onChunk, onDone, onError) {
    fetch('/api/agent/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(response => {
      if (!response.ok) return response.json().then(e => { throw new Error(e.error); });
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      const read = () => {
        reader.read().then(({ done, value }) => {
          if (done) { onDone(); return; }
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop();
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const payload = line.slice(6).trim();
            if (payload === '[DONE]') { onDone(); return; }
            try {
              const obj = JSON.parse(payload);
              if (obj.text) onChunk(obj.text);
              if (obj.error) onError(obj.error);
            } catch {}
          }
          read();
        }).catch(onError);
      };
      read();
    }).catch(onError);
  }
};
