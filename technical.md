# BA intelligence

| **Actor**             | **Chatbot should ask**                           |
| :-------------------- | :----------------------------------------------- |
| **Actor**             | "Who is performing this action?"                 |
| **Action detail**     | "Can you describe exactly how this should work?" |
| **Expected result**   | "What should happen after this action?"          |
| **Failure condition** | "What should happen if this fails?"              |
| **Business reason**   | "Why is this needed?"                            |

---

**26/06/2026 - Log**

---

- Created `vocab.json`,`vocab.py` files to handle language logic

  ### `vocab.py`,`vocab.json`

  ```Python
  with open('AIRE_project/AIRE/vocab.json', 'r') as f:
    file = json.load(f)
    BASIC_CONV = [] # Keys of Basic conversation [Hi,Hello...]
    QUES = [] # Keys of question parameters[1,2,3...]
    for x, y in file.items():
        if x != 'question':
            BASIC_CONV.append(x)
        else:
            for p, q in file['question'].items():
                QUES.append(p)
    nlp = spacy.load('en_core_web_md')
  ```

  **Note :**

  > This Script took the keys of Basic conversation strings, question keys from `vocab.json` and store it inside `BASIC_CONV `, `QUES`

  > from today I am going to use `vocab.json` as container of vocabulary parameters in `JSON` formate.

---

**27/06/2026 - Log**

---

- Created more efficiant `JSON` thath can response to greetings
- Struncture of JSON:

  ```JSON
  {
  "greetings": {
    "short_simple": {
      "category": "Short & Simple (1-2 words)",
      "words": []
    },
    "casual_slang": {
      "category": "Casual & Slang",
      "words": []
    },
    "time_based": {
      "category": "Time-Based Greetings",
      "words": []
    },
    "polite_formal": {
      "category": "Polite & Formal",
      "words": []
    },
    "indian_regional": {
      "category": "Indian & Regional Greetings",
      "words": []
    },
    "warm_friendly": {
      "category": "Warm & Friendly",
      "words": []
    },
    "checking_in": {
      "category": "Checking In (Beyond Just Hello)",
      "words": []
    },
    "international": {
      "category": "One-Word International Greetings",
      "words": []
    }
  },
  "respons": {
    "common": {
      "short_simple": "",
      "casual_slang": "",
      "time_based": "",
      "polite_formal": "",
      "indian_regional": "",
      "warm_friendly": "",
      "checking_in": "",
      "international": ""
    },
    "question": {
      "1": "",
      "2": "",
      "3": "",
      "4": "",
      "5": ""
    }
  }
  }

  ```

- Introduced new function `greet()` in `vocab.py` its return
  - **max_similarity_value** : With `.similarity(doc)` build in function of `spaCy` used to find the similarity of the prompt
  - **similar_greet_type** : Selecting the most suitable type of greeting type
  - **response** : Selecting the response
- Modified `CSS` for assign specific yellow color to the bubble of chat

| chack Box | Description                                                                                                                                      |
| :-------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| [x] l     | Instead of list of words ex:- `['Hi', 'Hello', 'Namasthe']` generating `spacy` synonims so that's can more intelligence                          |
| [ ] l     | Like the `greet()` function, introducing new functionality that select suitable question response once the Bot detect the lacks in requirenments |
| [ ] l     | Still trying yo implement the forms and labeled text box for collect information more pricisely.                                                 |

# Ambiguity intelligence

---

**10/08/2026 - Log**

---

Today I was created a Multilty Task Learning `Deep Neural Network` Model which is trained using `Cornelius_2025_user_story_ambiguity_dataset`, It has Lot's of class imbalance spesifically in the `Ambiguity = True` Dataset, however I find more effective threshold value for each of the ambiguity type and uses `Synthetic Data sets` with the support of LLMs like `Chat-GPT` and `Grok`

For feature extration from the text I used `sentence-transformer/all-MiniLM-L6-v2` `huggin-face` model.

# Constructing Chat-Bot Respose

---

**20/08/2026 - Log**

---

With those models I constructed a Structured Dictionary:

```Python
{
    'domain':'',
    'text' : {
        'id1':{
          'sentence':'string',
          'requirement_type': 'Functional',
          'requiremnt_type_confidance':float
        },
        'id2':{
          'sentence':'string',
          'requirement_type': 'non-Functional',
          'requiremnt_type_confidance':float
        },
        'id2':{
          'sentence':'string',
          'requirement_type': 'Functional',
          'requiremnt_type_confidance':float
        },
    },
    # SemanticAmbiguity,ScopeAmbiguity,ActorAmbiguity <--- if these three are None that is not gonna included into this JSON
    'requirements':{
        'Performance' : {
            'NumbersOfSentances' : num,
            'SemanticAmbiguity' : ['id1','id2'],
            'ScopeAmbiguity' : ['id1','id2'],
            'ActorAmbiguity' : ['id1','id2'],
        },
        'Usability' : {
            'NumbersOfSentances' : num,
            'SemanticAmbiguity' : ['id1','id2'],
            'ScopeAmbiguity' : ['id1','id2'],
            'ActorAmbiguity' : ['id1','id2'],
        },
        'Security' : {
            'SemanticAmbiguity' : ['id1','id2'],
            'ScopeAmbiguity' : ['id1','id2'],
            'ActorAmbiguity' : ['id1','id2'],
        },
        'Functional' : {
            'NumbersOfSentances' : num,
            'SemanticAmbiguity' : ['id1','id2'],
            'ScopeAmbiguity' : ['id1','id2'],
            'ActorAmbiguity' : ['id1','id2'],
        },
        'Operational' : {
            'NumbersOfSentances' : num,
            'SemanticAmbiguity' : ['id1','id2'],
            'ScopeAmbiguity' : ['id1','id2'],
            'ActorAmbiguity' : ['id1','id2'],
        },
        'Non-Functional' : {
            'NumbersOfSentances' : num,
            'SemanticAmbiguity' : ['id1','id2'],
            'ScopeAmbiguity' : ['id1','id2'],
            'ActorAmbiguity' : ['id1','id2'],
        },
    }
}
```

Generate some templates with `Chat-GPT` for client friendly chat-bot response:

- AMBIGUITY_INITIAL_PROMPTS
- AMBIGUITY_DESCRIPTIONS
- AMBIGUITY_CLARIFICATION_QUESTIONS

Finally I construct a template based chat-bot respose:

```cmd
Detected Ambiguities(Interactive Labels) : ['ActorAmbiguity', 'SemanticAmbiguity', 'ScopeAmbiguity']

Your requirement has unclear boundaries, so it is not clear exactly what is included. It contains unclear or subjective terms that may be understood differently. It does not clearly identify who should perform this action.

Specifically, You have mentioned,

    -----------------------------------------------------------------------------
    administrators should handle problems reported by customers and monitor the performance of sellers.
    -----------------------------------------------------------------------------
    In here actually,
(1) What exactly do you mean by this term or phrase?
(2) Could you provide a specific example of what you expect?
(3) Can you replace this general term with a specific value, condition, or time?
(4) What specific result would you consider acceptable?
(5) How would you describe this requirement so that everyone understands it in the same way?

    -----------------------------------------------------------------------------
    we operate an online marketplace with many sellers. customers should be able to find products and place orders, while sellers need to manage the products they offer and update their orders. the company also wants reports to understand sales activity. administrators should handle problems reported by customers and monitor the performance of sellers.
    -----------------------------------------------------------------------------
    In here actually,
(1) What exactly should this feature include?
(2) Who should this requirement apply to?
(3) Are there any users, activities, or situations that should be excluded?
(4) Are there any limits or conditions on when this feature should be used?
(5) What should the system do outside the scope of this requirement?

    -----------------------------------------------------------------------------
    we operate an online marketplace with many sellers.
    -----------------------------------------------------------------------------
    In here actually,
(1) Who should perform this action?
(2) Which user role or staff member is responsible for this activity?
(3) Who should be allowed to use this feature?
(4) Can more than one role perform this action?
(5) Who should be responsible when this action requires approval?
```

# Integrating with chat-bot UI

---

**24/08/2026 - Log**

---

Today I made some changes in the UI of the chat-bot and connected the AI models, It sends responses to the JavaScript, in here the server is the `routes.py` and the reciever is `chat.js` the `chat.js` send a `request` as `POST` method to the `routes.py` and the `routes.py` feed it to the AI-models,

### `routes.py` request reciever

```python
data = request.get_json(silent=True) or {}
    requirement_text = (data.get("message") or "").strip()

```

The above script used for take request from the `chat.js` and the below script is the response,

```python
 response_payload = {
        "status": status,
        "token": token,
        "label": label,
        "ambiguous": ambiguous,
        "reply": reply_text,
        "vocab": Vocab
    }
```

### `chat.js` request sender

This `chat.js` read the chat form `DOM` element of the `index.html`

**`index.html` Form element**

```html
<form class="composer m-1 p-2 rounded-pill" id="composer" autocomplete="off">
  <input type="text" id="messageInput" placeholder="e.g. The system should let admins reset a user's password" autocomplete="off" />
  <button type="submit" id="sendBtn" aria-label="Send">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path d="M3 11L21 3L13 21L11 13L3 11Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round" />
    </svg>
  </button>
</form>
```

**`chat.js` request sending script to the server**

```javascript
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
```
