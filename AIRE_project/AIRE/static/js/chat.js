// AIRE Requirement Intake — front-end logic
// Talks to /api/chat, renders responses, no LLM logic here —
// all classification happens server-side via the ML engine.

const thread = document.getElementById("thread");
const composer = document.getElementById("composer");
const input = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");

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

function questions(ambiguity, token) {
  let questions_string = "";
  Object.entries(vocab.respons.AMBIGUITY_CLARIFICATION_QUESTIONS[ambiguity]).forEach(([key, val]) => {
    let dataCard = `${ambiguity}_${token}_${parseInt(key) + 1}`;
    questions_string += `
    <div class="question-item">
      <div class="question-number">${parseInt(key) + 1}</div>
      <div class="question-content">
        <div class="question-text qn-${parseInt(key) + 1}" id = "${ambiguity}">${val}</div>
        <div class="answer-field-wrap d-flex">
          <textarea
            class="answer-field token-${token} qn-${parseInt(key) + 1}"
            name = "${ambiguity}_${parseInt(key) + 1}"
            rows="1"
            placeholder="e.g. Search by category, price filter, and wishlist..."
            oninput="
              autoResize(this);
              checkProgress('${token}');
            "
            data-card="${dataCard}"
          ></textarea>
        </div>
      </div>
    </div>
    `;
  });
  return questions_string;
}
let vocab = "";
let DATA = "";

function addBotMessage(data, statusClass, metaText) {
  DATA = data;
  vocab = data.vocab;
  const currentToken = data.token; // Keep local track of token

  const msg = document.createElement("div");
  msg.className = `msg msg--bot ${statusClass ? "msg--" + statusClass : ""}`;
  msg.id = `msg-${currentToken}`; // Prefixed ID to prevent conflicts with invalid CSS selectors

  if (data.label == "greeting") {
    msg.innerHTML = `
      <div class="msg-label">AIRE</div>
      <div class="bubble">${data.reply}</div>
      ${metaText ? `<div class="meta-tag">${metaText}</div>` : ""}
    `;
  } else if (data.label == "question" || data.ambiguous > 0) {
    let str = "";
    data.reply.DETECTED_AMBIGUITES.forEach((ambiguity) => {
      str += `
        <div class="ambiguity-card">
          <div class="ambiguity-card-header">
            <div class="ambiguity-type-icon icon-scope"><div class='p-2 border border-info rounded'></div></div>
            <div>
              <div class="ambiguity-type-label">${ambiguity}</div>
              <div class="ambiguity-type-desc">"${data.reply.GROUPED_BY_AMBIGUITY[ambiguity]}"</div>
            </div>
          </div>
          <div class="ambiguity-card-body">
            ${questions(ambiguity, currentToken)}
          </div>
        </div>
      `;
    });

    // Notice token-specific IDs for progress fill & label
    msg.innerHTML = `
      <div class="msg-label">AIRE</div>
      <div class="bubble msg-row">
        <div class="badge-row">
          <span class="aire-badge badge-domain">${data.reply.DOMAIN}</span>
          <span class="aire-badge badge-ambiguity-count">⚠ ${data.reply.DETECTED_AMBIGUITES.length} Ambiguities Detected</span>
        </div>

        <div class="ambiguity-alert">${data.reply.DESCRIPTION}</div>
        <div class="clarification-progress-label">
          <span>Clarification progress</span>
          <span id="progressLabel-${currentToken}">0 / 0 Questions answered</span>
        </div>
        <div class="clarification-progress">
          <div class="clarification-progress-fill" id="progressFill-${currentToken}"></div>
        </div>
        <div id="form_${currentToken}">
          <div class="ambiguity-section">
            <div class="ambiguity-section-title">Clarification Required</div>
            ${str}
          </div>
          <div class="submit-all-row">
            <button class="btn-aire-ghost" onclick="skipAll('${currentToken}')">Skip for now</button>
            <button class="btn-aire-primary" onclick="submitAll('${currentToken}')">✓ Submit Clarifications</button>
          </div>
        </div>
      </div>
      <div class="meta-tag">${metaText || ""}</div>    
    `;
  }

  document.getElementById("thread").appendChild(msg);
  scrollToBottom();
}
function clientAnswer(data) {
  if (Object.keys(data).length === 0) return;
  const questionArr = [];
  const answerArr = [];
  const ambiguities = [];
  const formElement = document.getElementById(`form_${data.token}`);
  const questions = formElement.querySelectorAll(".question-text");
  const answers = formElement.querySelectorAll(".answer-field");

  questions.forEach((element) => {
    questionArr.push(element.textContent);
    ambiguities.push(element.id);
  });
  answers.forEach((element) => {
    answerArr.push(element.value.trim());
  });
  console.log("Questions:", questionArr);
  console.log("Ambiguities:", ambiguities);
  console.log("Answers:", answerArr);
  // answerArr.forEach((val) => {
  //   if (val == "") {
  //     let idx = answerArr.indexOf(val);
  //     console.log(idx, val);
  //     questionArr.splice(idx, 1);
  //     answerArr.splice(idx, 1);
  //   }
  // });
  return [questionArr, answerArr, ambiguities];
}
async function sendAnswers(res) { //Sending cooked JSON to Database
  try {
    const resplonse = await fetch("/api/database", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(res),
    });

    if (!resplonse.ok) {
      console.log("STATUS:", resplonse.statusText);
    }
  } catch (error) {
    console.log("ERROR:", error);
  }
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
      addBotMessage(data || "Something went wrong⚠️. Please try again.", "queued", null);
      return;
    }

    const metaText = `token ${data.token} · label ${data.label} · ambiguous ${data.ambiguous}`;
    addBotMessage(data, data.status, metaText);
  } catch (err) {
    removeThinkingBubble();
    addBotMessage("Connection issue❌ couldn't reach the back-end.", "queued", null);
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

// ── Auto resize textarea ──────────────────────────────────────────────────
function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 120) + "px";
}

// ── Progress tracking ─────────────────────────────────────────────────────
function checkProgress(token) {
  const fields = document.querySelectorAll(`.token-${token}`);
  if (fields.length === 0) return;

  let answered = 0;
  fields.forEach((field) => {
    if (field.value.trim().length > 0) {
      answered++;
    }
  });

  const pct = Math.round((answered / fields.length) * 100);

  // Targets token-specific progress UI elements
  const progressFill = document.getElementById(`progressFill-${token}`);
  const progressLabel = document.getElementById(`progressLabel-${token}`);

  if (progressFill) progressFill.style.width = pct + "%";
  if (progressLabel) progressLabel.textContent = `${answered} / ${fields.length} Questions answered`;
}

// ── Submit all clarifications ─────────────────────────────────────────────
function submitAll(token) {
  const textAreas = document.querySelectorAll(`.token-${token}`);
  textAreas.forEach((input) => {
    input.disabled = true;
  });
  const [questions, answers, ambiguities] = clientAnswer(DATA);
  const obj = {
    questions: questions, //Array
    answers: answers, //Array
    ambiguities: ambiguities, //Array
    session: {
      status: DATA.status, //String
      token: DATA.token, //String
      label: DATA.label, //String
      ambiguous: DATA.ambiguous, //int
      reply: DATA.reply, //Object
    },
  };
  sendAnswers(obj); // Storing to DB
  const tokenMsg = document.createElement("div");
  tokenMsg.className = "msg msg--bot queued";
  tokenMsg.innerHTML = `
    <div class="msg-label">AIRE</div>
    <div class="bubble">
      ✅ Thank you, your clarifications have been recorded. A Business Analyst will review your requirement and we will follow up shortly. Your token number is <strong>#${token}</strong>.
    </div>`;

  const thread = document.getElementById("thread");
  thread.appendChild(tokenMsg);
  thread.scrollTop = thread.scrollHeight;
}

// ── Skip ──────────────────────────────────────────────────────────────────
function skipAll(token) {
  const thread = document.getElementById("thread");

  const skipMsg = document.createElement("div");
  skipMsg.className = "msg msg--user";
  skipMsg.innerHTML = `
    <div class="msg-label">You</div>
    <div class="bubble">I'll clarify these later.</div>`;

  thread.appendChild(skipMsg);

  // Target the container by prefixed message ID
  const botCard = document.getElementById(`msg-${token}`);
  if (botCard) botCard.style.display = "none";

  const tokenMsg = document.createElement("div");
  tokenMsg.className = "msg msg--bot queued";
  tokenMsg.innerHTML = `
    <div class="msg-label">AIRE</div>
    <div class="bubble">Understood. Your requirement has been saved with token <strong>#${token}</strong>.
      Our team will reach out to clarify the open points.</div>`;

  thread.appendChild(tokenMsg);
  thread.scrollTop = thread.scrollHeight;
}

// BA_DASHBOARD---------------------------------------------------------------------------------------------

// BA_DASHBOARD---------------------------------------------------------------------------------------------
