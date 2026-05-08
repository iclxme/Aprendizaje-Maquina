const messagesEl = document.getElementById("messages");
const emptyStateEl = document.getElementById("empty-state");
const form = document.getElementById("composer");
const input = document.getElementById("input");
const sendButton = document.getElementById("send");
const newChatButton = document.getElementById("new-chat");

let isLoading = false;

function setLoading(nextValue) {
  isLoading = nextValue;
  input.disabled = nextValue;
  sendButton.disabled = nextValue;
  sendButton.textContent = nextValue ? "Pensando..." : "Enviar";
}

function syncEmptyState() {
  emptyStateEl.hidden = messagesEl.children.length > 0;
}

function scrollToLatest() {
  messagesEl.lastElementChild?.scrollIntoView({ block: "end", behavior: "smooth" });
}

function autoResizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
}

function appendMessage(role, text, options = {}) {
  const item = document.createElement("li");
  item.className = `message ${role}${options.error ? " error" : ""}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  item.appendChild(bubble);

  if (options.sources?.length) {
    bubble.appendChild(renderSources(options.sources));
  }

  messagesEl.appendChild(item);
  syncEmptyState();
  scrollToLatest();
  return bubble;
}

function renderSources(sources) {
  const wrapper = document.createElement("div");
  wrapper.className = "sources";

  const title = document.createElement("div");
  title.className = "sources-title";
  title.textContent = "Fuentes consultadas";
  wrapper.appendChild(title);

  const list = document.createElement("ol");
  list.className = "sources-list";

  sources.slice(0, 4).forEach((source) => {
    const item = document.createElement("li");
    const label = source.document || source.category || source.chunk_id || "Fuente";
    const detail = source.source_section ? ` - ${source.source_section}` : "";

    if (source.canonical_url) {
      const link = document.createElement("a");
      link.href = source.canonical_url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = `${label}${detail}`;
      item.appendChild(link);
    } else {
      item.textContent = `${label}${detail}`;
    }

    list.appendChild(item);
  });

  wrapper.appendChild(list);
  return wrapper;
}

async function sendQuestion(question) {
  const pendingBubble = appendMessage("assistant", "Pensando...");
  setLoading(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || "No se pudo obtener respuesta del backend.");
    }

    const body = await response.json();
    pendingBubble.textContent = body.answer || "Sin respuesta.";

    if (body.sources?.length) {
      pendingBubble.appendChild(renderSources(body.sources));
    }
  } catch (error) {
    pendingBubble.parentElement.classList.add("error");
    pendingBubble.textContent =
      "No pude conectar con el backend. Revisa que FastAPI, Ollama y la base RAG esten disponibles.";
  } finally {
    setLoading(false);
    input.focus();
    scrollToLatest();
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (isLoading) return;

  const question = input.value.trim();
  if (!question) return;

  appendMessage("user", question);
  input.value = "";
  autoResizeInput();
  await sendQuestion(question);
});

input.addEventListener("input", autoResizeInput);

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

newChatButton.addEventListener("click", () => {
  if (isLoading) return;
  messagesEl.replaceChildren();
  syncEmptyState();
  input.value = "";
  autoResizeInput();
  input.focus();
});

syncEmptyState();
autoResizeInput();
