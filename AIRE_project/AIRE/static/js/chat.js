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
        <div class="msg-label">AIRES</div>
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
        <div class="question-text reqCategory qn-${parseInt(key) + 1}" id = "${ambiguity}">${val}</div>
        <div class="answer-field-wrap d-flex">
          <textarea
            class="answer-field reqCategory token-${token} qn-${parseInt(key) + 1}"
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
      <div class="msg-label">AIRES</div>
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
      <div class="msg-label">AIRES</div>
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
            <div class="ambiguity-section-title">Fill this section to get in touch</div>
            <div class="ambiguity-alert" id="heyWaitsec"></div>
            <div class = "ambiguity-card">
              <div class = "ambiguity-card-body" id = "personalizedQuestions">
                <div class="question-item">
                  <div class="question-number">1</div>
                  <div class="question-content">
                    <div class="question-text qn-1" id = "name">Name</div>   
                    <div class="answer-field-wrap d-flex">
                      <input
                        class="answer-field token-${currentToken} qn-1"
                        name = "name"
                        placeholder="John Doe"
                      ></input>
                    </div>
                  </div>
                </div>
                <div class="question-item">
                  <div class="question-number">2</div>
                  <div class="question-content">
                    <div class="question-text qn-2" id = "phone">Phone Number</div>
                    <div class="answer-field-wrap d-flex">
                      <input
                        class="bot answer-field token-${currentToken} qn-2"
                        name = "phone"
                        placeholder="+94XXXXXXXXX"
                      ></input>
                    </div>
                  </div>
                </div>
                <div class="question-item">
                  <div class="question-number">3</div>
                  <div class="question-content">
                    <div class="question-text qn-3" id = "company">Your Company</div>
                    <div class="answer-field-wrap d-flex">
                      <input
                        class="bot answer-field token-${currentToken} qn-3"
                        name = "company"
                        placeholder="Ex: ABC (Pvt) Ltd"
                      ></input>
                    </div>
                  </div>
                </div>
                <div class="question-item">
                  <div class="question-number">4</div>
                  <div class="question-content">
                    <div class="question-text qn-4" id = "job">Job title</div>
                    <div class="answer-field-wrap d-flex">
                      <input
                        class="answer-field token-${currentToken} qn-4"
                        name = "job"
                        placeholder="Ex: Employee (Business Analyst)"
                      ></input>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="submit-all-row">
            <a id="redirectToform" href="" class="btn-aire-primary" onclick="formSubmission('${currentToken}')">Submit a Form</a>
            <button class="btn-aire-primary" onclick="submitAll('${currentToken}')">✓ Submit Clarifications</button>
          </div>
        </div>
      </div>
      <div class="meta-tag">${metaText || ""}</div>    
    `;
  }

  document.getElementById("thread").appendChild(msg);
  scrollToBottom();
  heywaitAsec(currentToken);
}

let duplicatedData = { company: "", user: "" };

function heywaitAsec(duplicatedToken) {
  const personalizedQuestions = document.getElementById("personalizedQuestions");
  if (!personalizedQuestions) return;

  // 1. Target inputs reliably using the HTML classes (.qn-3 for Company, .qn-2 for Phone)
  const companyInput = personalizedQuestions.querySelector("input.qn-3");
  const phoneInput = personalizedQuestions.querySelector("input.qn-2");
  const suggestMessage = document.getElementById("heyWaitsec");

  if (!companyInput || !phoneInput || !suggestMessage) return;

  let debounceTimer = null;

  // ── A. COMPANY INPUT LISTENER ───────────────────────────────────────────
  companyInput.addEventListener("input", (e) => {
    const inputValue = e.target.value.trim();
    clearTimeout(debounceTimer);

    if (!inputValue) {
      suggestMessage.innerHTML = "";
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const response = await fetch("/waitasec", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          // Send NAME explicitly; include token only if present
          body: JSON.stringify({ NAME: inputValue, TOKEN: duplicatedToken || "" }),
        });

        if (!response.ok) {
          console.error("HTTP Error:", response.statusText);
          return;
        }

        const data = await response.json();
        const companyData = data.company;
        suggestMessage.innerHTML = ""; // Clear previous render

        // Check if company_name array exists and has matches
        if (companyData?.company_name && Array.isArray(companyData.company_name) && companyData.company_name.length > 0) {
          const title = document.createElement("div");
          title.className = "ambiguity-alert";
          title.innerHTML = "If your company is already registered, pick the name below:";
          suggestMessage.appendChild(title);

          for (let i = 0; i < companyData.company_name.length; i++) {
            const currentCompany = companyData.company_name[i];
            const currentEmail = companyData.billing_email ? companyData.billing_email[i] : null;

            const badge = document.createElement("span");
            badge.className = "badge text-bg-warning me-1 mt-1 p-2";
            badge.style.cursor = "pointer";
            badge.textContent = currentEmail ? `${currentCompany} | ${currentEmail}` : `${currentCompany}`;

            // Populate input field on badge click
            badge.addEventListener("click", () => {
              companyInput.value = currentCompany;
              duplicatedData = data;
              suggestMessage.innerHTML = ""; // Clear badges after selection
            });

            suggestMessage.appendChild(badge);
          }
        }
      } catch (error) {
        console.error("Fetch Error:", error);
      }
    }, 300);
  });

  // ── B. PHONE INPUT LISTENER ──────────────────────────────────────────────
  phoneInput.addEventListener("input", (e) => {
    const inputValue = e.target.value.trim();
    clearTimeout(debounceTimer);

    if (!inputValue) {
      suggestMessage.innerHTML = "";
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const response = await fetch("/waitasec", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ PHONE: inputValue, TOKEN: duplicatedToken || "" }),
        });

        if (!response.ok) {
          console.error("HTTP Error:", response.statusText);
          return;
        }

        const data = await response.json();
        const userData = data.user;
        suggestMessage.innerHTML = ""; // Clear previous render

        // Check if existing user records match the phone number
        if (userData?.id && Array.isArray(userData.id) && userData.id.length > 0) {
          const tokenWrapper = document.createElement("div");
          tokenWrapper.className = "mt-2";
          tokenWrapper.innerHTML = `
            <label class="question-text prevtoken d-block small mb-1">
              If you already partially registered, add your last token number:
            </label>
            <input class="answer-field prevtoken form-control" placeholder="Enter Token No" />
          `;
          suggestMessage.appendChild(tokenWrapper);
          duplicatedData = data;
        }
      } catch (error) {
        console.error("Fetch Error:", error);
      }
    }, 300);
  });
}
function clientAnswer(data) {
  if (Object.keys(data).length === 0) return;
  const questionArr = [];
  const answerArr = [];
  const personalizedAnswers = [];
  const ambiguities = [];
  const formElement = document.getElementById(`form_${data.token}`);
  const personalizedQuestions = document.getElementById("personalizedQuestions");
  const questions = formElement.querySelectorAll(".question-text.reqCategory");
  const answers = formElement.querySelectorAll(".answer-field.reqCategory");
  //Requirement Q & A
  questions.forEach((element) => {
    questionArr.push(element.textContent);
    ambiguities.push(element.id);
  });
  answers.forEach((element) => {
    answerArr.push(element.value.trim());
  });

  // Personalized Q & A
  personalizedQuestions.querySelectorAll(".answer-field").forEach((element) => {
    personalizedAnswers.push(element.value.trim());
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
  return [questionArr, answerArr, ambiguities, personalizedAnswers];
}
async function sendAnswers(res) {
  //Sending cooked JSON to Database
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
  const [questions, answers, ambiguities, personalizedAnswers] = clientAnswer(DATA);
  const obj = {
    questions: questions,
    answers: answers,
    ambiguities: ambiguities,
    personalizedAnswers: personalizedAnswers,
    duplicate: duplicatedData,
    session: {
      status: DATA.status,
      token: DATA.token,
      label: DATA.label,
      ambiguous: DATA.ambiguous,
      reply: DATA.reply,
    },
  };
  const tokenMsg = document.createElement("div");
  tokenMsg.className = "msg msg--bot queued";

  if (!personalizedAnswers.includes("")) {
    document.getElementById("redirectToform").href = "form";

    // ── SAFELY AUTO-FILL FORM INPUTS ──────────────────────────────────
    const regForm = document.querySelector(".regForm");

    // Only attempt to fill if the form element actually exists on the DOM
    if (regForm && duplicatedData) {
      // 1. Fill User Fields
      if (duplicatedData.user && typeof duplicatedData.user === "object") {
        Object.keys(duplicatedData.user).forEach((key) => {
          const inputEl = regForm.querySelector(`.${key}`);
          const valueArr = duplicatedData.user[key];

          if (inputEl && valueArr) {
            // Handle if value is an array or string
            inputEl.value = Array.isArray(valueArr) ? valueArr[0] || "" : valueArr;
          }
        });
      }

      // 2. Fill Company Fields
      if (duplicatedData.company && typeof duplicatedData.company === "object") {
        Object.keys(duplicatedData.company).forEach((key) => {
          const inputEl = regForm.querySelector(`.${key}`);
          const valueArr = duplicatedData.company[key];

          if (inputEl && valueArr) {
            // Handle if value is an array or string
            inputEl.value = Array.isArray(valueArr) ? valueArr[0] || "" : valueArr;
          }
        });
      }
    } else {
      // If form is on a different page (e.g., redirecting to 'form'), save to localStorage
      localStorage.setItem("duplicatedData", JSON.stringify(duplicatedData));
    }
    // ──────────────────────────────────────────────────────────────────

    htmlStr = `
    <div class="msg-label">AIRES</div>
    <div class="bubble">
      ✅ Thank you <strong>${personalizedAnswers[0]}</strong>, your clarifications have been recorded. A Business Analyst will review your requirement and we will follow up shortly. Your token number is <strong>#${token}</strong>.
    </div>`;
    sendAnswers(obj); // Storing to DB
    textAreas.forEach((input) => {
      input.disabled = true;
    });
  } else {
    const personalizedQuestions = document.getElementById("personalizedQuestions");
    personalizedQuestions.querySelectorAll(".answer-field").forEach((element) => {
      element.style.border = "1px solid red";
      document.getElementById("redirectToform").href = "#";
    });
    htmlStr = `
    <div class="msg-label">AIRES</div>
    <div class="bubble">
      Please fill those required fields ⚠️
    </div>`;
  }

  tokenMsg.innerHTML = htmlStr;

  const thread = document.getElementById("thread");
  thread.appendChild(tokenMsg);
  thread.scrollTop = thread.scrollHeight;

  return personalizedAnswers;
}

// ── formSubmission ──────────────────────────────────────────────────────────────────
async function formSubmission(token) {
  const [Name, Phone, Company, Job] = submitAll(token);
  const pastToken = document.querySelector(".answer-field.prevtoken");
  let payload;

  if (pastToken && pastToken.value.trim() !== "") {
    payload = {
      payloadStatus: 1,
      tokenNo: pastToken.value.trim(),
    };
  } else {
    payload = {
      payloadStatus: 2,
      tokenNo: token,
      Name: Name,
      Phone: Phone,
      Company: Company,
      Job: Job,
    };
  }

  try {
    const response = await fetch("/form", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      const result = await response.json();
      console.log("Server Response:", result);
    } else {
      console.error("Server returned non-200 status:", response.status);
    }
  } catch (error) {
    console.error("Fetch Error:", error);
  }
}

// BA_DASHBOARD---------------------------------------------------------------------------------------------

// BA_DASHBOARD---------------------------------------------------------------------------------------------
