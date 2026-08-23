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
from AIRE import app
from AIRE.models import requirements, ba_outputs
from AIRE.ml_engine import classify_requirement
from AIRE.label_mapper import map_label_to_response

# Confidence threshold for ambiguity trigger (see project context)
CONFIDENCE_THRESHOLD = 0.85

# In-memory store for submitted requirements (token -> data)
# Swap for a real DB later; kept simple on purpose.
REQUIREMENTS_STORE = {}


@app.route("/")
def index():
    """Serve the chatbot UI."""
    return render_template("index.html")


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
    confidence = ml_result["confidence"]
    label = ml_result["label"]
    greet_res = ml_result["response"]

    # --- LABEL MAPPING ---
    mapped_sentence = map_label_to_response(label, greet_res)

    token = "Not set"

    # --- ROUTING LOGIC (per project spec) ---
    if label == 'greeting':
        reply_text = mapped_sentence
        status = "Greet"
    elif confidence > 0:
        # Confident enough to ask a clarifying question back to the client
        reply_text = mapped_sentence
        status = "clarify"
    else:
        token = str(uuid.uuid4())[:8].upper()
        # Storing into DB
        REQUIREMENTS_STORE[token] = {
            # inside here we have to store the result_df in the Final_Production.ipynb with Q&A
            "text": requirement_text,
            "label": label,
            "confidence": confidence,
        }
        # Not confident - log it and tell the client we'll follow up
        reply_text = f"Thanks! We've logged your requirement (Token: {token}). Our team will contact you shortly."
        status = "queued"

    response_payload = {
        "status": status,
        "token": token,
        "label": label,
        "confidence": round(confidence, 2),
        "reply": reply_text
    }

    return jsonify(response_payload)
