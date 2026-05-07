const API_BASE = 'http://127.0.0.1:8000';

const messagesEl = document.getElementById('messages');
const form = document.getElementById('composer');
const input = document.getElementById('input');

function appendMessage(text, cls = '') {
  const li = document.createElement('li');
  li.textContent = text;
  if (cls) li.classList.add(cls);
  messagesEl.appendChild(li);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const q = input.value.trim();
  if (!q) return;
  appendMessage(q, 'user');
  input.value = '';
  appendMessage('...', '');
  const lastBot = messagesEl.querySelector('li:last-child');
  try {
    const res = await fetch(API_BASE + '/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q })
    });
    if (!res.ok) {
      lastBot.textContent = 'Error: ' + (await res.text());
      return;
    }
    const body = await res.json();
    lastBot.textContent = body.answer || 'Sin respuesta';
  } catch (err) {
    lastBot.textContent = 'Error: ' + err.message;
  }
});

// health-check on load
(async () => {
  try {
    const r = await fetch(API_BASE + '/health');
    if (!r.ok) throw new Error('backend no disponible');
  } catch (e) {
    appendMessage('No se pudo conectar al backend. Inicia el servidor en http://127.0.0.1:8000');
  }
})();
