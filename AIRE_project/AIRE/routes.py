"""
AIRE - AI Requirement Engineering
Flask back-end for the chatbot UI.

Flow implemented here:
    INPUT (chatbot text) -> FLASK -> ML ENGINE (stub) -> FLASK -> JSON -> OUTPUT (chatbot reply)

NOTE: ml_engine.classify_requirement() is currently a placeholder.
Replace its internals with the real scikit-learn model calls when ready.
Nothing in this file should need to change when that happens - it only
expects {"confidence": float, "label": str, "message": str} back.
"""

# from flask import Flask, render_template, request, jsonify
# import uuid
# from ml_engine import classify_requirement
# from label_mapper import map_label_to_response
# app = Flask(__name__)

from flask import render_template, request, jsonify
import uuid
from AIRE import app, db
from AIRE.vocab import Vocab
from AIRE.query import reconstruct_payload
from AIRE.models import save_session_payload, Session, Sentence, Clarification, AmbiguityResult
from AIRE.ml_engine import classify_requirement
from AIRE.label_mapper import map_label_to_response
import json

# In-memory store for submitted requirements (token -> data)
# Swap for a real DB later; kept simple on purpose.
REQUIREMENTS_STORE = {}


@app.route("/")
def index():
    """Serve the chatbot UI."""
    return render_template("index.html")


@app.route("/api/database", methods=["POST"])
def adder():
    data = request.get_json(silent=True) or {}
    que = data.get("questions")
    ans = data.get("answers")
    # print(data)
    try:
        save_session_payload(data)
        db.session.commit()
        return {"status": "success"}, 200

    except Exception as e:
        db.session.rollback()
        print(f"DB Error: {e}")
        return {"status": "error", "message": str(e)}, 500


@app.route("/dashboard")
def dashboard_page():
    sessions = Session.query.order_by(Session.submitted_at.desc()).all()
    tokens = [s.token for s in sessions]
    default_payload = reconstruct_payload(tokens[0]) if tokens else {}

    # Renders the full HTML template
    return render_template("ba_dashboard.html", tokens=tokens, user=default_payload)


@app.route("/api/dashboard", methods=["POST"])
def api_dashboard():
    data = request.get_json(silent=True) or {}
    token = (data.get("tokenNo") or "").strip()

    payload = reconstruct_payload(token)
    with open("data.json", "w") as f:
        f.write(json.dumps(payload))
    return jsonify(payload)  # Returns JSON data for fetch()


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Receives a client requirement typed into the chatbot.
    Sends it to the ML engine, maps the resulting label to a
    response sentence, and returns a unified JSON payload.
    """
    data = request.get_json(silent=True) or {}
    requirement_text = (data.get("message") or "").strip()

    if not requirement_text:
        return jsonify({
            "status": "error",
            "reply": "Please type a requirement before sending."
        }), 400

    # --- ML ENGINE ---
    ml_result = classify_requirement(requirement_text)
    ambiguous = ml_result["ambiguous"]
    label = ml_result["label"]
    dict_res = ml_result["response"]
    # --- LABEL MAPPING ---
    mapped_sentence = map_label_to_response(label, dict_res)

    token = "Not set"

    # --- ROUTING LOGIC (per project spec) ---
    if label == 'greeting':
        reply_text = mapped_sentence
        status = "Greet"
    elif ambiguous > 0:
        # Confident enough to ask a clarifying question back to the client
        reply_text = dict_res
        status = "clarify"
        print(reply_text)
        token = str(uuid.uuid4())[:8].upper()
    else:
        token = str(uuid.uuid4())[:8].upper()
        # Storing into DB
        REQUIREMENTS_STORE[token] = {
            # inside here we have to store the result_df in the Final_Production.ipynb with Q&A
            "text": requirement_text,
            "label": label,
            "ambiguous": ambiguous,
        }
        # Not confident - log it and tell the client we'll follow up
        reply_text = f"Understood. Your requirement has been saved with token <strong>{token}</strong>.Our team will reach out to clarify the open points."
        status = "queued"

    response_payload = {
        "status": status,
        "token": token,
        "label": label,
        "ambiguous": ambiguous,
        "reply": reply_text,
        "vocab": Vocab
    }
    with open('TEST.json', 'w') as f:
        f.write(json.dumps(response_payload))
    return json.dumps(response_payload)
