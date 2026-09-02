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

from flask import render_template, request, jsonify, redirect, url_for
from flask_wtf import FlaskForm  # for form
from wtforms import StringField, PasswordField, SubmitField, SelectField, URLField  # for form
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError  # for Form Validation
import uuid
from AIRES import app, db
from AIRES.vocab import Vocab
from AIRES.query import reconstruct_payload, reconstruct_company_payload, company_query, user_query
from AIRES.ml_engine import classify_requirement
from AIRES.models import save_session_payload, Session, Sentence, Clarification, AmbiguityResult, Company, User
from AIRES.label_mapper import map_label_to_response
import json

# In-memory store for submitted requirements (token -> data)
# Swap for a real DB later; kept simple on purpose.
REQUIREMENTS_STORE = {}


@app.route("/")
def index():
    """Serve the chatbot UI."""
    return render_template("index.html")


@app.route("/api/database", methods=["POST", "GET"])
def adder():
    data = request.get_json(silent=True) or {}
    with open("data.json", "w") as f:
        f.write(json.dumps(data))
    # print(data)
    try:
        save_session_payload(data)
        db.session.commit()
        return {"status": "success"}, 200

    except Exception as e:
        db.session.rollback()
        print(f"DB Error: {e}")
        return {"status": "error", "message": str(e)}, 500


@app.route("/waitasec", methods=["POST", "GET"])
def wait_a_second():
    data = request.get_json(silent=True) or {}

    company_name = (data.get("NAME") or "").strip()
    phone_no = (data.get("PHONE") or "").strip()
    token = (data.get("TOKEN") or "").strip()

    payload = {
        "company": company_query(name=company_name, token=token) if (company_name or token) else {},
        "user": user_query(phone=phone_no, token=token) if (phone_no or token) else {}
    }

    return jsonify(payload)


class RegisterForm(FlaskForm):
    # Form fields MUST be declared at the Class Level
    name = StringField(label="Name:", validators=[Length(min=2, max=30), DataRequired()])
    phone_number = StringField(label="Phone Number:", validators=[Length(min=10), DataRequired()])
    job_title = StringField(label="Job Title:", validators=[DataRequired()])
    email = StringField(label="Personal Email:", validators=[DataRequired()])

    company_name = StringField(label="Company Name:", validators=[Length(min=2, max=30), DataRequired()])
    industry = StringField(label="Industry:", validators=[Length(min=2, max=30), DataRequired()])
    company_size = SelectField(
        'Company Size',
        choices=[('1', 'Micro Enterprise'), ('2', 'Small Business'),
                 ('3', 'Medium Enterprise'), ('4', 'Large Enterprise')]
    )
    website_url = URLField(label="Website URL:", validators=[DataRequired()])
    billing_email = StringField(label="Company Email:", validators=[DataRequired()])
    submit = SubmitField(label='Register')

    def __init__(self, session_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = session_id

        # Populate pre-existing data from DB if available and form isn't submitted yet
        if not self.is_submitted():
            company_record = db.session.query(Company).filter(Company.session_id == session_id).first()
            user_record = db.session.query(User).filter(User.session_id == session_id).first()

            if user_record:
                self.name.data = self.name.data or user_record.name
                self.phone_number.data = self.phone_number.data or user_record.phone_number
                self.job_title.data = self.job_title.data or user_record.job_title
                self.email.data = self.email.data or user_record.email

            if company_record:
                self.company_name.data = self.company_name.data or company_record.company_name
                self.industry.data = self.industry.data or company_record.industry
                self.company_size.data = self.company_size.data or company_record.company_size
                self.website_url.data = self.website_url.data or company_record.website_url
                self.billing_email.data = self.billing_email.data or company_record.billing_email

    def validate_phone_number(self, phone_field):
        existing_user = User.query.filter_by(phone_number=phone_field.data).first()
        # Only raise error if phone belongs to ANOTHER session
        if existing_user and existing_user.session_id != self.session_id:
            raise ValidationError('This Phone number is already registered.')

    def validate_billing_email(self, email_field):
        # Target Company model instead of User model
        existing_company = Company.query.filter_by(billing_email=email_field.data).first()
        if existing_company and existing_company.session_id != self.session_id:
            raise ValidationError('Entered Company Email is already in use.')


@app.route("/fromRes")
def response():
    return redirect(url_for("response"))


# @app.route("/form", methods=["POST", "GET"])
# def form():
#     data = request.get_json(silent=True) or {}
#     payload_status = data.get("payloadStatus")  # Expecting integer 1 or 2
#     token = str(data.get("tokenNo") or "").strip()

#     initial_data = {}

#     if payload_status == 2:
#         initial_data = {
#             "name": (data.get("Name") or "").strip(),
#             "phone_number": (data.get("Phone") or "").strip(),
#             "job_title": (data.get("Job") or "").strip(),
#             "company_name": (data.get("Company") or "").strip(),
#         }

#     # Instantiate form passing token and extracted values
#     myForm = RegisterForm(session_id=token, data=initial_data)

#     if myForm.validate_on_submit():

#         # 1. UPSERT Company
#         company_record = Company.query.filter_by(session_id=token).first() or Company(session_id=token)
#         company_record.company_name = myForm.company_name.data
#         company_record.industry = myForm.industry.data
#         company_record.company_size = myForm.company_size.data
#         company_record.website_url = myForm.website_url.data
#         company_record.billing_email = myForm.billing_email.data
#         db.session.add(company_record)

#         # Send pending operations to DB so company_record gets its .id populated
#         db.session.flush()

#         # 2. UPSERT User
#         user_record = User.query.filter_by(session_id=token).first() or User(session_id=token)
#         user_record.name = myForm.name.data
#         user_record.phone_number = myForm.phone_number.data
#         user_record.job_title = myForm.job_title.data
#         user_record.email = myForm.email.data

#         # Now company_record.id is guaranteed to have an integer value
#         user_record.company_id = company_record.id

#         db.session.add(user_record)
#         db.session.commit()

#         # return jsonify({"status": "success", "message": "Form submitted successfully!"})
#         return redirect(url_for("fromRes"))

#     return render_template("form.html", form=myForm)

@app.route("/form", methods=["POST", "GET"])
def form():
    # 1. Handle incoming JSON payload if pre-filling from an external request
    data = request.get_json(silent=True) or {}
    payload_status = data.get("payloadStatus")
    token = str(data.get("tokenNo") or request.args.get("token") or "").strip()

    initial_data = {}
    if payload_status == 2:
        initial_data = {
            "name": (data.get("Name") or "").strip(),
            "phone_number": (data.get("Phone") or "").strip(),
            "job_title": (data.get("Job") or "").strip(),
            "company_name": (data.get("Company") or "").strip(),
        }

    # 2. Instantiate form properly
    # If request is POST, Flask-WTF automatically picks up request.form.
    # Otherwise (GET), pre-populate using formdata/initial_data.
    if request.method == "POST":
        myForm = RegisterForm()
    else:
        myForm = RegisterForm(data=initial_data)

    # 3. Validate submission
    if myForm.validate_on_submit():
        # Retrieve token from form if passed in hidden field, or fallback to token variable
        token_val = token

        # 1. UPSERT Company
        company_record = Company.query.filter_by(
            session_id=token_val
        ).first() or Company(session_id=token_val)
        company_record.company_name = myForm.company_name.data
        company_record.industry = myForm.industry.data
        company_record.company_size = myForm.company_size.data
        company_record.website_url = myForm.website_url.data
        company_record.billing_email = myForm.billing_email.data
        db.session.add(company_record)

        db.session.flush()

        # 2. UPSERT User
        user_record = User.query.filter_by(session_id=token_val).first() or User(
            session_id=token_val
        )
        user_record.name = myForm.name.data
        user_record.phone_number = myForm.phone_number.data
        user_record.job_title = myForm.job_title.data
        user_record.email = myForm.email.data
        user_record.company_id = company_record.id

        db.session.add(user_record)
        db.session.commit()

        # Successfully redirects after submission
        return redirect(url_for("response"))

    return render_template("form.html", form=myForm, token=token)


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
    # with open("data.json", "w") as f:
    #     f.write(json.dumps(payload))
    return jsonify(payload)  # Returns JSON data for fetch()


@app.route("/company-dashboard")
def company_dashboard_page():
    companies = Company.query.order_by(Company.company_name, Company.id).all()
    default_payload = reconstruct_company_payload(companies[0].id) if companies else {}
    return render_template(
        "ba_dashboard_comany.html",
        companies=companies,
        user=default_payload,
    )


@app.route("/api/company-dashboard", methods=["POST"])
def api_company_dashboard():
    data = request.get_json(silent=True) or {}
    try:
        company_id = int(data.get("companyId"))
    except (TypeError, ValueError):
        return jsonify({"error": "companyId must be an integer"}), 400

    return jsonify(reconstruct_company_payload(company_id))


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
