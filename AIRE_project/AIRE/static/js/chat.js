// AIRE Requirement Intake — front-end logic
// Talks to /api/chat, renders responses, no LLM logic here —
// all classification happens server-side via the ML engine.

const thread = document.getElementById("thread");
const composer = document.getElementById("composer");
const input = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const lastMeta = document.getElementById("lastMeta");

function scrollToBottom() {
  thread.scrollTop = thread.scrollHeight;
}

// Client message
function addUserMessage(text) {
  const msg = document.createElement("div");
  msg.className = "msg msg--user";
  msg.innerHTML = `
        <div class="msg-label">You</div>
        <div class="bubble"></div>
    `;
  msg.querySelector(".bubble").textContent = text;
  thread.appendChild(msg);
  scrollToBottom();
}

// Bot message
function addThinkingBubble() {
  const msg = document.createElement("div");
  msg.className = "msg msg--bot";
  msg.id = "thinkingBubble";
  msg.innerHTML = `
        <div class="msg-label">AIRE</div>
        <div class="bubble thinking"><span></span><span></span><span></span></div>
    `;
  thread.appendChild(msg);
  scrollToBottom();
}

function removeThinkingBubble() {
  const el = document.getElementById("thinkingBubble");
  if (el) el.remove();
}

function addBotMessage(text, statusClass, metaText) {
  const msg = document.createElement("div");
  msg.className = `msg msg--bot ${statusClass ? "msg--" + statusClass : ""}`;
  msg.innerHTML = `
        <div class="msg-label">AIRE</div>
        <div class="bubble"></div>
        ${metaText ? `<div class="meta-tag"></div>` : ""}
    `;
  msg.querySelector(".bubble").textContent = text;
  if (metaText) msg.querySelector(".meta-tag").textContent = metaText;
  thread.appendChild(msg);
  scrollToBottom();
}

async function sendMessage(text) {
  addUserMessage(text);
  input.value = "";
  sendBtn.disabled = true;
  addThinkingBubble();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    const data = await response.json();
    removeThinkingBubble();

    if (!response.ok) {
      addBotMessage(data.reply || "Something went wrong. Please try again.", "queued", null);
      return;
    }

    const metaText = `token ${data.token} · label ${data.label} · confidence ${data.confidence}`;
    addBotMessage(data.reply, data.status, metaText);
    lastMeta.textContent = metaText;
  } catch (err) {
    removeThinkingBubble();
    addBotMessage("Connection issue — couldn't reach the back-end.", "queued", null);
    console.error(err);
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

composer.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  sendMessage(text);
});

input.focus();
