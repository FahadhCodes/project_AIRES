<div align="center">

# 🤖 AIRES

### Artificial Intelligence Requirement Elicitation System

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.21-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)](https://tensorflow.org)
[![spaCy](https://img.shields.io/badge/spaCy-3.8-09A3D5?style=for-the-badge&logo=spacy&logoColor=white)](https://spacy.io)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)

> **AI-powered web system that bridges the gap between unstructured client requirements and structured software artifacts.**

AIRES analyses raw requirement text submitted through a chatbot interface, classifies each sentence by requirement type, detects multiple categories of ambiguity using deep-learning models, and guides the client through clarifying questions — all in real time.

</div>

---

## 📑 Table of Contents

- [Screenshots](#-screenshots)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [ML Pipeline](#-ml-pipeline)
- [Tech Stack](#-tech-stack)
- [ER Diagram](#-er-diagram)
- [API Routes](#-api-routes)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Target Users](#-target-users)
- [Project Status](#-project-status)
- [Development Timeline](#-development-timeline)

---

## 📸 Screenshots

<div align="center">

<table>
  <tr>
    <td align="center"><b>🏠 Chatbot Landing Page</b></td>
  </tr>
  <tr>
    <td><img src="image.png" width="700" alt="AIRES Chatbot Landing Page"/></td>
  </tr>
</table>

<table>
  <tr>
    <td align="center"><b>💬 Ambiguity Detection & Clarification</b></td>
    <td align="center"><b>📊 BA Analytics Dashboard</b></td>
  </tr>
  <tr>
    <td><img src="image-1.png" width="420" alt="Chatbot Ambiguity Detection"/></td>
    <td><img src="image-2.png" width="420" alt="BA Dashboard"/></td>
  </tr>
</table>

</div>

---

## ✨ Key Features

| Feature                               | Description                                                                                                                           |
| :------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------ |
| 🧠 **Requirement Classification**     | SVM classifier with TF-IDF + domain keywords identifies requirement types (Functional, Security, Performance, Usability, Operational) |
| 🔍 **Multi-Task Ambiguity Detection** | Keras DNN with 4 output heads detects Semantic, Scope, Actor & Process Execution ambiguities                                          |
| 💬 **Intelligent Chatbot**            | spaCy-powered greeting engine + structured clarification Q&A flow                                                                     |
| 📊 **BA Dashboard**                   | Per-session & per-company analytics with requirement distribution charts and ambiguity flags                                          |
| 🏢 **Client Management**              | Company & user registration with duplicate detection and auto-fill                                                                    |
| 🗄️ **Full Persistence**               | SQLite database with 6 normalised tables via SQLAlchemy ORM                                                                           |

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    subgraph CLIENT["Client Layer"]
        UI["index.html - Chatbot UI"]
        DASH["ba_dashboard.html - BA Dashboard"]
        CDASH["ba_dashboard_company.html - Company Dashboard"]
        FORM["form.html - Registration Form"]
    end

    subgraph JS["Frontend Logic"]
        CHATJS["chat.js - Handles user input, renders bot replies"]
    end

    subgraph FLASK["Flask Backend"]
        ROUTES["routes.py - API Endpoints"]
        QUERY["query.py - Payload Reconstruction"]
        MAPPER["label_mapper.py - Label to Response"]
    end

    subgraph ML["ML Engine"]
        ENGINE["ml_engine.py - classify requirement"]
        GREET["vocab.py greet - spaCy Similarity"]
        BABRAIN["BA Brain - TF-IDF + SVM"]
        AMBIGUITY["Ambiguity Detector - Keras Multi-Task DNN"]
        SBERT["Sentence-Transformers - all-MiniLM-L6-v2"]
    end

    subgraph DB["Database"]
        SQLITE["SQLite via SQLAlchemy"]
        MODELS["models.py - ORM + save session payload"]
    end

    UI --> CHATJS
    CHATJS -- "POST /api/chat" --> ROUTES
    ROUTES --> ENGINE
    ENGINE --> GREET
    ENGINE --> BABRAIN
    ENGINE --> AMBIGUITY
    AMBIGUITY --> SBERT
    ENGINE -- "response" --> ROUTES
    ROUTES --> MAPPER
    ROUTES -- "JSON payload" --> CHATJS
    CHATJS -- "POST /api/database" --> ROUTES
    ROUTES --> MODELS
    MODELS --> SQLITE
    DASH --> ROUTES
    CDASH --> ROUTES
    ROUTES --> QUERY
    QUERY --> SQLITE
    FORM -- "POST /form" --> ROUTES

    style CLIENT fill:#0d1b2a,stroke:#00d4ff,color:#fff
    style JS fill:#1b2838,stroke:#ffa500,color:#fff
    style FLASK fill:#1a1a2e,stroke:#e94560,color:#fff
    style ML fill:#16213e,stroke:#0f3460,color:#fff
    style DB fill:#1a1a2e,stroke:#53d769,color:#fff
```

---

## 🧠 ML Pipeline

```mermaid
flowchart LR
    INPUT["Raw Requirement Paragraph"] --> SENT["Sentence Splitter - spaCy sententizer"]

    SENT --> BRANCH1["TF-IDF + Domain Keywords"]
    SENT --> BRANCH2["Sentence Embedding - all-MiniLM-L6-v2"]

    BRANCH1 --> SVM["BA Brain - SVM Classifier"]
    SVM --> RTYPE["Requirement Type: Functional, Security, Performance, Usability, Operational"]

    BRANCH2 --> DNN["Multi-Task DNN - Keras Model"]

    DNN --> HEAD1["Head 1: HasAmbiguity - Binary"]
    DNN --> HEAD2["Head 2: Domain - Telecom, Finance, E-commerce, Healthcare, Manufacturing"]
    DNN --> HEAD3["Head 3: Ambiguity Subtypes - Semantic, Scope, Actor"]
    DNN --> HEAD4["Head 4: Process Execution - Binary"]

    RTYPE --> RESPONSE["Structured Response"]
    HEAD1 --> RESPONSE
    HEAD2 --> RESPONSE
    HEAD3 --> RESPONSE
    HEAD4 --> RESPONSE

    RESPONSE --> BOT["Bot Reply + Clarification Questions"]

    style INPUT fill:#0d1b2a,stroke:#00d4ff,color:#fff
    style SVM fill:#1a1a2e,stroke:#ffa500,color:#fff
    style DNN fill:#16213e,stroke:#e94560,color:#fff
    style RESPONSE fill:#1a1a2e,stroke:#53d769,color:#fff
    style BOT fill:#0d1b2a,stroke:#00d4ff,color:#fff
```

### Neural Network Architecture (Netron)

<div align="center">
  <img src="multitask_ambiguity_model.keras.svg" width="800" alt="Multi-Task Ambiguity Model — Netron Visualization"/>
  <br/>
  <sub><i>Multi-Task DNN architecture exported from Netron — 4 output heads for ambiguity detection</i></sub>
</div>

<br/>

### Model Details

| Model                  | Algorithm                         | Input                 | Output                        | Artifacts                                             |
| :--------------------- | :-------------------------------- | :-------------------- | :---------------------------- | :---------------------------------------------------- |
| **BA Brain**           | SVM + TF-IDF + domain keywords    | Preprocessed sentence | Requirement type + confidence | `ba_brain_model.pkl`, `ba_brain_tfidf.pkl`            |
| **Ambiguity Detector** | Multi-task DNN (4 heads)          | Sentence embeddings   | Ambiguity flags per type      | `multitask_ambiguity_model.keras`, `edge_values.json` |
| **Greeting Engine**    | Cosine similarity (spaCy vectors) | User message          | Greeting type + response      | `vocab.json`                                          |

> **Training Data**: `Cornelius_2025_user_story_ambiguity_dataset` augmented with synthetic data generated via ChatGPT & Grok to address class imbalance in ambiguity-positive samples.

---

## 🛠️ Tech Stack

```mermaid
flowchart LR
    subgraph Frontend
        HTML["HTML5"]
        CSS["CSS3"]
        JSS["JavaScript"]
    end

    subgraph Backend
        FLASK2["Flask 3.1"]
        WTF["Flask-WTF"]
        SA["SQLAlchemy"]
    end

    subgraph AI_ML["AI and ML"]
        TF["TensorFlow"]
        KERAS["Keras"]
        SKLEARN["scikit-learn"]
        SPACY["spaCy"]
        ST["Sentence-Transformers"]
    end

    subgraph Data
        SQLITE2["SQLite"]
        PANDAS["pandas"]
        NUMPY["NumPy"]
    end

    Frontend --> Backend
    Backend --> AI_ML
    Backend --> Data
    AI_ML --> Data

    style Frontend fill:#0d1b2a,stroke:#00d4ff,color:#fff
    style Backend fill:#1a1a2e,stroke:#e94560,color:#fff
    style AI_ML fill:#16213e,stroke:#ffa500,color:#fff
    style Data fill:#1a1a2e,stroke:#53d769,color:#fff
```

---

## 🗃️ ER Diagram

```mermaid
erDiagram
    sessions ||--o{ sentences : "has many"
    sessions ||--o{ ambiguity_results : "has many"
    sessions ||--o{ clarifications : "has many"
    sessions ||--o{ companies : "linked to"
    sessions ||--o{ users : "linked to"
    companies ||--o{ users : "employs"
    sentences ||--o{ ambiguity_results : "flagged with"

    sessions {
        string token PK
        string status
        string domain
        int ambiguity_count
        text raw_paragraph
        datetime submitted_at
        datetime updated_at
    }

    sentences {
        int id PK
        string session_id FK
        int sentence_index
        text raw_text
        string requirement_type
        float confidence_score
        boolean has_ambiguity
        datetime created_at
    }

    ambiguity_results {
        int id PK
        string session_id FK
        int sentence_id FK
        string ambiguity_type
        boolean detected
        datetime created_at
    }

    clarifications {
        int id PK
        string session_id FK
        string ambiguity_type
        text question
        text answer
        boolean answered
        datetime created_at
        datetime answered_at
    }

    companies {
        int id PK
        string session_id FK
        string company_name
        string industry
        string company_size
        string website_url
        string billing_email
        datetime created_at
    }

    users {
        int id PK
        string session_id FK
        int company_id FK
        string name
        string phone_number
        string job_title
        string email
        datetime created_at
    }
```

---

## 🔌 API Routes

```mermaid
flowchart LR
    subgraph Pages["Page Routes"]
        R1["GET /"]
        R2["GET /dashboard"]
        R3["GET /company-dashboard"]
        R4["GET-POST /form"]
    end

    subgraph APIs["API Endpoints"]
        A1["POST /api/chat"]
        A2["POST /api/database"]
        A3["POST /api/dashboard"]
        A4["POST /api/company-dashboard"]
        A5["POST /waitasec"]
    end

    R1 -- "Chatbot UI" --> A1
    A1 -- "ML analysis" --> A2
    R2 -- "Session view" --> A3
    R3 -- "Company view" --> A4
    R4 -- "Registration" --> A5

    style Pages fill:#0d1b2a,stroke:#00d4ff,color:#fff
    style APIs fill:#1a1a2e,stroke:#e94560,color:#fff
```

| Route                    |  Method  | Description                                                    |
| :----------------------- | :------: | :------------------------------------------------------------- |
| `/`                      |   GET    | Chatbot UI — requirement intake console                        |
| `/api/chat`              |   POST   | Core ML API — accepts `{ "message": "..." }`, returns analysis |
| `/api/database`          |   POST   | Persists full session payload to SQLite                        |
| `/dashboard`             |   GET    | BA dashboard — per-session analytics                           |
| `/api/dashboard`         |   POST   | Fetch reconstructed payload for a given token                  |
| `/company-dashboard`     |   GET    | BA dashboard — per-company aggregate view                      |
| `/api/company-dashboard` |   POST   | Fetch company payload by `companyId`                           |
| `/form`                  | GET/POST | Client registration form (Flask-WTF)                           |
| `/waitasec`              |   POST   | Duplicate-check lookup for company/user pre-fill               |

---

## 📁 Project Structure

```
Project/
├── 📄 README.md                         ← you are here
├── 📄 technical.md                      development logs & design notes
├── 📄 requirements.txt                  pip dependencies
├── 🖼️ image.png                         chatbot landing screenshot
├── 🖼️ image-1.png                       ambiguity detection screenshot
├── 🖼️ image-2.png                       BA dashboard screenshot
│
└── project_AIRES/
    ├── 🚀 run.py                        Flask entry point
    ├── 📄 pyproject.toml                package metadata
    ├── 📄 dev-requirements.txt          dev-only deps
    ├── 🧪 tests/                        unit tests & fixtures
    │
    └── AIRES/                           main application package
        ├── __init__.py                  Flask app + SQLAlchemy init
        ├── routes.py                    all Flask routes
        ├── models.py                    ORM models + save_session_payload()
        ├── ml_engine.py                 classify_requirement() orchestrator
        ├── vocab.py                     NLP pipeline (greet, classify, detect)
        ├── label_mapper.py              ML label → human response
        ├── query.py                     DB → payload reconstruction
        │
        ├── 🤖 ba_brain_model.pkl        trained SVM classifier
        ├── 🤖 ba_brain_tfidf.pkl        fitted TF-IDF vectoriser
        ├── 🤖 multitask_ambiguity_model.keras  multi-task Keras DNN
        ├── 📊 edge_values.json          decision thresholds
        ├── 📊 vocab.json                greeting vocab & templates
        ├── 📊 domain_vocab.json         domain keyword features
        ├── 📊 requirement_classifier.json
        │
        ├── templates/                   Jinja2 HTML
        │   ├── index.html               chatbot page
        │   ├── ba_dashboard.html        session dashboard
        │   ├── ba_dashboard_comany.html  company dashboard
        │   ├── form.html                registration form
        │   └── fromRes.html             confirmation page
        │
        └── static/
            ├── css/style.css            UI styles
            └── js/chat.js               chatbot client logic
```

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/FahadhCodes/project_AIRES.git
cd project_AIRES

# 2. Create & activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r ../requirements.txt

# 4. Start the server
python run.py
```

> 🌐 The app launches at **http://localhost:5000**

---

## 👥 Target Users

| Role                     | How AIRES Helps                                                                          |
| :----------------------- | :--------------------------------------------------------------------------------------- |
| 🏢 **Clients**           | Chat anytime, submit requirements in plain English, track progress via unique tokens     |
| 📋 **Business Analysts** | Receive structured, classified requirements with ambiguity reports and clarification Q&A |
| 📈 **Project Managers**  | Evaluate scope, cost, and timeline with clearer initial requirements                     |
| 🧪 **QA Engineers**      | Start from unambiguous, classified requirements to write better test cases               |
| 💻 **Developers**        | Build from well-defined, non-overlapping requirement specifications                      |

---

## 📋 Project Status

| Milestone                                                         |     Status     |
| :---------------------------------------------------------------- | :------------: |
| Goal formulation & user stories                                   |    ✅ Done     |
| Data model design (6 tables)                                      |    ✅ Done     |
| Vocabulary & greeting engine (spaCy NLP)                          |    ✅ Done     |
| Requirement type classifier (TF-IDF + SVM)                        |    ✅ Done     |
| Multi-task ambiguity detector (Keras DNN + Sentence-Transformers) |    ✅ Done     |
| Chatbot UI (HTML/CSS/JS ↔ Flask API)                              |    ✅ Done     |
| BA Dashboard (per-session & per-company views)                    |    ✅ Done     |
| Client registration form (Flask-WTF)                              |    ✅ Done     |
| SQLite persistence via SQLAlchemy                                 |    ✅ Done     |
| User/company duplicate detection & pre-fill                       |    ✅ Done     |
| **MVP v1 complete**                                               |  ✅ **Done**   |
| Production hardening & final release                              | 🔧 In progress |

---

## 📅 Development Timeline

```mermaid
flowchart LR
    A["Jun 2026 - Vocab Engine, spaCy greeting detection"] --> B["Aug 10 - Ambiguity DNN, Multi-task model trained"]
    B --> C["Aug 20 - Response Builder, Structured dict + templates"]
    C --> D["Aug 24 - UI Integration, Chatbot and Flask API connected"]
    D --> E["Sep 2026 - MVP v1, Dashboards + Forms + SQLite"]

    style A fill:#0d1b2a,stroke:#00d4ff,color:#fff
    style B fill:#16213e,stroke:#ffa500,color:#fff
    style C fill:#1a1a2e,stroke:#e94560,color:#fff
    style D fill:#16213e,stroke:#53d769,color:#fff
    style E fill:#0d1b2a,stroke:#00d4ff,color:#fff
```

> 📝 Detailed development logs and design decisions are documented in [`technical.md`](technical.md).

---

<div align="center">

**Built with ❤️ using Flask, TensorFlow, spaCy & scikit-learn**

</div>
