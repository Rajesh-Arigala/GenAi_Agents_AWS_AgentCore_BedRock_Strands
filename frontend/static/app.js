const messages = document.querySelector("#messages");
const chatForm = document.querySelector("#chatForm");
const promptInput = document.querySelector("#prompt");
const userIdInput = document.querySelector("#userId");
const sessionIdInput = document.querySelector("#sessionId");
const sendButton = document.querySelector("#sendButton");
const statusPill = document.querySelector("#statusPill");

function ensureSessionId() {
  if (!sessionIdInput.value.trim()) {
    sessionIdInput.value = `web-${crypto.randomUUID()}`;
  }
}

function formatAnswer(text) {
  const escaped = text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");

  return escaped
    .split(/\n{2,}/)
    .map((paragraph) => `<p>${paragraph.replaceAll("\n", "<br>")}</p>`)
    .join("");
}

function addMessage(role, text, meta = "") {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "You" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = formatAnswer(text);

  if (meta) {
    const metaLine = document.createElement("small");
    metaLine.textContent = meta;
    bubble.appendChild(metaLine);
  }

  article.append(avatar, bubble);
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

function setBusy(isBusy) {
  sendButton.disabled = isBusy;
  promptInput.disabled = isBusy;
  statusPill.classList.toggle("busy", isBusy);
  statusPill.querySelector("span:last-child").textContent = isBusy
    ? "Invoking runtime"
    : "Runtime ready";
}

async function sendPrompt(prompt) {
  ensureSessionId();
  addMessage("user", prompt);
  const pending = addMessage("assistant", "Invoking AgentCore Runtime...");
  setBusy(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        user_id: userIdInput.value.trim() || "guest",
        session_id: sessionIdInput.value.trim(),
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || data.error || "Request failed");
    }

    pending.querySelector(".bubble").innerHTML = formatAnswer(data.answer || "");
    const metaLine = document.createElement("small");
    metaLine.textContent = `${data.mode} | ${data.user_id} | ${data.session_id}`;
    pending.querySelector(".bubble").appendChild(metaLine);
  } catch (error) {
    pending.querySelector(".bubble").innerHTML = formatAnswer(
      `Invocation failed: ${error.message}`
    );
    pending.classList.add("error");
  } finally {
    setBusy(false);
    promptInput.focus();
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const prompt = promptInput.value.trim();
  if (!prompt) return;
  promptInput.value = "";
  sendPrompt(prompt);
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    promptInput.value = button.dataset.prompt;
    promptInput.focus();
  });
});

ensureSessionId();
