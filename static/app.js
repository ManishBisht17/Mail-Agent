const messagesEl = document.getElementById("messages");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const resetBtn = document.getElementById("reset-btn");

let isLoading = false;
let welcomeRemoved = false;

const TOOL_LABELS = {
  read_emails: "Read emails",
  send_email: "Send email",
  label_email: "Label email",
  summarize_email: "Summarize email",
};

const WELCOME_HTML = `
  <div class="welcome">
    <div class="welcome-card">
      <div class="welcome-icon">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="2" y="4" width="20" height="16" rx="2"/>
          <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
        </svg>
      </div>
      <h2>How can I help with your inbox?</h2>
      <p>Read, summarize, send, or organize your emails — just ask naturally or pick a suggestion below.</p>
      <div class="suggestion-chips">
        <button class="chip" data-prompt="Read my latest unread emails">📬 Read unread emails</button>
        <button class="chip" data-prompt="Summarize my most recent unread email">📝 Summarize latest</button>
        <button class="chip" data-prompt="Help me compose a professional email reply">✍️ Compose a reply</button>
        <button class="chip" data-prompt="Label my latest email as Important">🏷️ Label as important</button>
      </div>
    </div>
  </div>
`;

function bindChips() {
  document.querySelectorAll(".chip, .action-btn").forEach((btn) => {
    btn.addEventListener("click", () => sendMessage(btn.dataset.prompt));
  });
}

function removeWelcome() {
  if (!welcomeRemoved) {
    const welcome = messagesEl.querySelector(".welcome");
    if (welcome) welcome.remove();
    welcomeRemoved = true;
  }
}

function autoResize() {
  messageInput.style.height = "auto";
  messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + "px";
}

function createMessage(role, content, toolsUsed = []) {
  removeWelcome();

  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "user" ? "You" : "AI";
  wrapper.appendChild(avatar);

  const body = document.createElement("div");
  body.className = "message-body";

  const label = document.createElement("div");
  label.className = "message-label";
  label.textContent = role === "user" ? "You" : "Mail Agent";
  body.appendChild(label);

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = content;
  body.appendChild(bubble);

  if (toolsUsed.length > 0) {
    const badges = document.createElement("div");
    badges.className = "tool-badges";
    toolsUsed.forEach((tool) => {
      const badge = document.createElement("span");
      badge.className = "tool-badge";
      badge.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
        </svg>
        ${TOOL_LABELS[tool.name] || tool.name}
      `;
      badges.appendChild(badge);
    });
    body.appendChild(badges);
  }

  wrapper.appendChild(body);
  messagesEl.appendChild(wrapper);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return wrapper;
}

function showTypingIndicator() {
  removeWelcome();
  const el = document.createElement("div");
  el.className = "message agent";
  el.id = "typing";
  el.innerHTML = `
    <div class="message-avatar">AI</div>
    <div class="message-body">
      <div class="message-label">Mail Agent</div>
      <div class="typing-indicator">
        <span></span><span></span><span></span>
      </div>
    </div>
  `;
  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function hideTypingIndicator() {
  const el = document.getElementById("typing");
  if (el) el.remove();
}

function setLoading(loading) {
  isLoading = loading;
  sendBtn.disabled = loading;
  messageInput.disabled = loading;
}

async function sendMessage(text) {
  const message = text.trim();
  if (!message || isLoading) return;

  createMessage("user", message);
  messageInput.value = "";
  autoResize();
  setLoading(true);
  showTypingIndicator();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    hideTypingIndicator();

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Something went wrong" }));
      createMessage("agent", `Error: ${err.detail}`, []).querySelector(".message-bubble").classList.add("error-bubble");
      return;
    }

    const data = await res.json();
    createMessage("agent", data.content, data.tools_used);
  } catch {
    hideTypingIndicator();
    const msg = createMessage("agent", "Could not reach the server. Is the backend running?");
    msg.querySelector(".message-bubble").classList.add("error-bubble");
  } finally {
    setLoading(false);
    messageInput.focus();
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage(messageInput.value);
});

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage(messageInput.value);
  }
});

messageInput.addEventListener("input", autoResize);

bindChips();

resetBtn.addEventListener("click", async () => {
  if (isLoading) return;
  try {
    await fetch("/api/reset", { method: "POST" });
  } catch { /* ignore */ }
  messagesEl.innerHTML = WELCOME_HTML;
  welcomeRemoved = false;
  bindChips();
  messageInput.focus();
});
