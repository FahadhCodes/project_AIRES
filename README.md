# AIRES — Artificial Intelligence Requirement Engineering System

> AI-powered web system that bridges the gap between unstructured client requirements and structured software artifacts.

AIRES analyses raw requirement text submitted through a chatbot interface, classifies each sentence by requirement type, detects multiple categories of ambiguity using deep-learning models, and guides the client through clarifying questions — all in real time.

---

## Current Project Status

| Milestone                                                         |     Status     |
| :---------------------------------------------------------------- | :------------: |
| Goal formulation & user stories                                   |    ✅ Done     |
| Data model design                                                 |    ✅ Done     |
| Vocabulary & greeting engine (spaCy NLP)                          |    ✅ Done     |
| Requirement type classifier (TF-IDF + SVM)                        |    ✅ Done     |
| Multi-task ambiguity detector (Keras DNN + Sentence-Transformers) |    ✅ Done     |
| Chatbot UI (HTML/CSS/JS ↔ Flask API)                              |    ✅ Done     |
| BA Dashboard (per-session & per-company views)                    |    ✅ Done     |
| Client registration form (Flask-WTF)                              |    ✅ Done     |
| SQLite persistence via SQLAlchemy                                 |    ✅ Done     |
| MVP v1 complete                                                   |    ✅ Done     |
| User/company duplicate detection & pre-fill                       |    ✅ Done     |
| Production hardening & final release                              | 🔧 In progress |

---

## Tech Stack

| Layer        | Technology                                                                                             |
| :----------- | :----------------------------------------------------------------------------------------------------- |
| **Backend**  | Flask 3.1, Flask-SQLAlchemy, Flask-WTF                                                                 |
| **Database** | SQLite (via SQLAlchemy ORM)                                                                            |
| **ML / NLP** | scikit-learn, TensorFlow / Keras, spaCy (`en_core_web_md`), Sentence-Transformers (`all-MiniLM-L6-v2`) |
| **Frontend** | Vanilla HTML, CSS, JavaScript (chatbot + dashboards)                                                   |
| **Data**     | pandas, NumPy, joblib, JSON vocab files                                                                |

---

## Project Structure

```
Project/
├── README.md                       # ← you are here
├── technical.md                    # development logs & design notes
├── requirements.txt                # pip dependencies
│
└── project_AIRES/
    ├── run.py                      # Flask entry point (creates DB & starts server)
    ├── pyproject.toml              # package metadata
    ├── dev-requirements.txt        # dev-only deps
    ├── tests/                      # unit tests & test fixtures
    │
    └── AIRES/                      # main application package
        ├── __init__.py             # Flask app factory + SQLAlchemy setup
        ├── routes.py               # all Flask routes (chatbot API, dashboards, forms)
        ├── models.py               # SQLAlchemy ORM models + save_session_payload()
        ├── ml_engine.py            # classify_requirement() — ties models together
        ├── vocab.py                # greeting engine, sententizer, BA brain, ambiguity pipeline
        ├── label_mapper.py         # maps ML labels to human-readable responses
        ├── query.py                # reconstruct_payload / reconstruct_company_payload helpers
        │
        ├── ba_brain_model.pkl      # trained requirement-type classifier (SVM)
        ├── ba_brain_tfidf.pkl      # fitted TF-IDF vectoriser
        ├── multitask_ambiguity_model.keras   # multi-task Keras DNN
        ├── edge_values.json        # optimal decision thresholds per ambiguity head
        ├── vocab.json              # greeting vocabulary & response templates
        ├── domain_vocab.json       # domain keyword feature lists
        ├── requirement_classifier.json  # domain keyword DataFrame
        │
        ├── templates/              # Jinja2 HTML templates
        │   ├── index.html          #   chatbot page
        │   ├── ba_dashboard.html   #   per-session BA dashboard
        │   ├── ba_dashboard_comany.html  # per-company BA dashboard
        │   ├── form.html           #   client registration form
        │   └── fromRes.html        #   post-submission confirmation
        │
        └── static/
            ├── css/style.css       # chatbot & dashboard styles
            └── js/chat.js          # chatbot client-side logic
```

---

## How It Works

```
Client types a requirement paragraph
            │
            ▼
     ┌─────────────┐
     │  chat.js     │  POST /api/chat  { "message": "..." }
     └──────┬──────┘
            │
            ▼
     ┌─────────────┐
     │  routes.py   │  receives JSON, calls classify_requirement()
     └──────┬──────┘
            │
            ▼
     ┌─────────────┐
     │ ml_engine.py │
     │  1. Greeting check (spaCy similarity)
     │  2. Sentence splitting & TF-IDF + domain keywords
     │  3. Requirement type classification (SVM)
     │  4. Sentence embedding (all-MiniLM-L6-v2)
     │  5. Multi-task ambiguity detection (Keras DNN)
     │     → HasAmbiguity, Domain, SemanticAmbiguity,
     │       ScopeAmbiguity, ActorAmbiguity,
     │       ProcessExecutionAmbiguity
     │  6. Template-based clarification response
     └──────┬──────┘
            │
            ▼
     ┌─────────────┐
     │  routes.py   │  returns JSON payload with:
     │              │    status, token, label, ambiguous,
     │              │    reply (structured), vocab
     └──────┬──────┘
            │
            ▼
     ┌─────────────┐
     │  chat.js     │  renders bot reply bubble
     │              │  (interactive ambiguity labels,
     │              │   clarification Q&A cards)
     └─────────────┘
            │
            ▼  POST /api/database  (full session payload)
     ┌─────────────┐
     │  models.py   │  persists to SQLite:
     │              │    sessions, sentences,
     │              │    ambiguity_results,
     │              │    clarifications,
     │              │    companies, users
     └─────────────┘
```

---

## Database Schema

| Table                 | Purpose                                                                              |
| :-------------------- | :----------------------------------------------------------------------------------- |
| **sessions**          | One record per client submission (token, status, domain, ambiguity count)            |
| **sentences**         | Individual sentences extracted from the paragraph (type, confidence, ambiguity flag) |
| **ambiguity_results** | Per-sentence ambiguity detections (Semantic, Scope, Actor, ProcessExecution)         |
| **clarifications**    | Question-answer pairs generated for ambiguous sentences                              |
| **companies**         | Client company information (name, industry, size, URL, billing email)                |
| **users**             | Client contact information (name, phone, job title, email) linked to a company       |

---

## ML Models

### 1. Requirement Type Classifier ("BA Brain")

- **Algorithm**: SVM with TF-IDF + domain keyword features
- **Artifacts**: `ba_brain_model.pkl`, `ba_brain_tfidf.pkl`
- **Output**: requirement type label (Functional, Security, Performance, Usability, Operational, Non-Functional) + confidence score

### 2. Multi-Task Ambiguity Detector

- **Architecture**: Deep Neural Network with four output heads
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
- **Training data**: `Cornelius_2025_user_story_ambiguity_dataset` + synthetic data (ChatGPT, Grok)
- **Artifact**: `multitask_ambiguity_model.keras`
- **Output heads**:
  1. `HasAmbiguity` — binary (is the sentence ambiguous at all?)
  2. `Domain` — multi-class (Telecommunications, Finance, E-commerce, Healthcare, Manufacturing)
  3. `AmbiguitySubtypes` — multi-label (Semantic, Scope, Actor)
  4. `ProcessExecutionAmbiguity` — binary
- **Thresholds**: tuned per head, stored in `edge_values.json`

### 3. Greeting / Conversational Engine

- **Library**: spaCy `en_core_web_md` word vectors
- **Method**: cosine similarity between user input and categorised greeting vocabulary
- **Vocabulary**: `vocab.json` (8 greeting categories + template responses)

---

## Pages & Routes

| Route                    |  Method  | Description                                   |
| :----------------------- | :------: | :-------------------------------------------- |
| `/`                      |   GET    | Chatbot UI                                    |
| `/api/chat`              |   POST   | Chatbot API — accepts `{ "message": "..." }`  |
| `/api/database`          |   POST   | Persists full session payload to SQLite       |
| `/dashboard`             |   GET    | BA dashboard (per-session view)               |
| `/api/dashboard`         |   POST   | Fetch reconstructed payload for a given token |
| `/company-dashboard`     |   GET    | BA dashboard (per-company aggregate view)     |
| `/api/company-dashboard` |   POST   | Fetch company payload by `companyId`          |
| `/form`                  | GET/POST | Client registration form (Flask-WTF)          |
| `/waitasec`              |   POST   | Duplicate-check lookup for company/user       |

---

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd Project/project_AIRES

# 2. Create & activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r ../requirements.txt

# 4. Run the server
python run.py
```

The app starts at **http://localhost:5000**.

---

## Target Users

| Role                  | How AIRES Helps                                                               |
| :-------------------- | :---------------------------------------------------------------------------- |
| **Clients**           | Chat anytime, submit requirements in plain English, track progress via tokens |
| **Business Analysts** | Receive structured, classified requirements with ambiguity reports            |
| **Project Managers**  | Evaluate scope, cost, and timeline with clearer initial requirements          |
| **QA Engineers**      | Start from unambiguous, classified requirements to write better test cases    |
| **Developers**        | Build from well-defined, non-overlapping requirements                         |

---

## Development Log

Detailed development logs and design decisions are documented in [`technical.md`].

Key milestones:

- **26–27 Jun 2026** — Vocabulary engine & greeting detection with spaCy
- **10 Aug 2026** — Multi-task ambiguity DNN trained & integrated
- **20 Aug 2026** — Structured response dictionary & template-based bot replies
- **24 Aug 2026** — Chatbot UI ↔ Flask API integration complete
- **Sep 2026** — BA dashboards, client registration, company views, SQLite persistence, MVP v1 shipped
