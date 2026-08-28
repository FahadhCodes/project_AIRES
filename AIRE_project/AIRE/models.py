"""
AIRE — SQLAlchemy ORM Models
BA Dashboard Database Schema
"""

from datetime import datetime
import json
from AIRE import db

# ── Table 1: Session ───────────────────────────────────────────────────────────
# One record per client submission (one paragraph = one session)


class Session(db.Model):
    __tablename__ = 'sessions'

    token = db.Column(db.String(16), primary_key=True)   # e.g. F7B66843
    status = db.Column(db.String(20),  nullable=False, default='clarify')  # clarify | resolved | pending
    domain = db.Column(db.String(50),  nullable=True)                 # E-commerce, Finance, etc.
    ambiguity_count = db.Column(db.Integer,     nullable=False, default=0)     # total ambiguous sentences
    raw_paragraph = db.Column(db.Text,        nullable=True)                 # original client paragraph
    submitted_at = db.Column(db.DateTime,    default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,    default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sentences = db.relationship('Sentence',        backref='session', lazy=True, cascade='all, delete-orphan')
    ambiguities = db.relationship('AmbiguityResult', backref='session', lazy=True, cascade='all, delete-orphan')
    clarifications = db.relationship('Clarification',   backref='session', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'token': self.token,
            'status': self.status,
            'domain': self.domain,
            'ambiguity_count': self.ambiguity_count,
            'submitted_at': self.submitted_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f'<Session token={self.token} status={self.status}>'


# ── Table 2: Sentence ──────────────────────────────────────────────────────────
# One record per sentence inside a session paragraph
class Sentence(db.Model):
    __tablename__ = 'sentences'

    id = db.Column(db.Integer,  primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(16),  db.ForeignKey('sessions.token'), nullable=False)
    sentence_index = db.Column(db.Integer,  nullable=False)               # position in paragraph (0,1,2...)
    raw_text = db.Column(db.Text,     nullable=False)               # original sentence
    requirement_type = db.Column(db.String(30), nullable=True)              # Functional, Security, etc.
    confidence_score = db.Column(db.Float,    nullable=True)                # BA Brain confidence
    has_ambiguity = db.Column(db.Boolean,  nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'sentence_index': self.sentence_index,
            'raw_text': self.raw_text,
            'requirement_type': self.requirement_type,
            'confidence_score': self.confidence_score,
            'has_ambiguity': self.has_ambiguity,
        }

    def __repr__(self):
        return f'<Sentence idx={self.sentence_index} type={self.requirement_type}>'


# ── Table 3: AmbiguityResult ───────────────────────────────────────────────────
# One record per ambiguity type detected per sentence
class AmbiguityResult(db.Model):
    __tablename__ = 'ambiguity_results'

    id = db.Column(db.Integer,  primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(16),  db.ForeignKey('sessions.token'), nullable=False)
    sentence_id = db.Column(db.Integer,  db.ForeignKey('sentences.id'), nullable=False)
    # SemanticAmbiguity | ScopeAmbiguity | ActorAmbiguity | etc.
    ambiguity_type = db.Column(db.String(40), nullable=False)
    detected = db.Column(db.Boolean,  nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship back to sentence
    sentence = db.relationship('Sentence', backref='ambiguity_results', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'sentence_id': self.sentence_id,
            'ambiguity_type': self.ambiguity_type,
            'detected': self.detected,
        }

    def __repr__(self):
        return f'<AmbiguityResult type={self.ambiguity_type} detected={self.detected}>'


# ── Table 4: Clarification ─────────────────────────────────────────────────────
# One record per question-answer pair submitted by client
class Clarification(db.Model):
    __tablename__ = 'clarifications'

    id = db.Column(db.Integer,  primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(16),  db.ForeignKey('sessions.token'), nullable=False)
    ambiguity_type = db.Column(db.String(40), nullable=False)   # which ambiguity this Q&A belongs to
    question = db.Column(db.Text,     nullable=False)     # the question asked to the client
    answer = db.Column(db.Text,     nullable=True)      # client's answer (nullable — may be skipped)
    answered = db.Column(db.Boolean,  nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answered_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'ambiguity_type': self.ambiguity_type,
            'question': self.question,
            'answer': self.answer,
            'answered': self.answered,
            'answered_at': self.answered_at.isoformat() if self.answered_at else None,
        }

    def __repr__(self):
        return f'<Clarification type={self.ambiguity_type} answered={self.answered}>'


# ── Helper: Save full payload to DB ───────────────────────────────────────────
def save_session_payload(payload: dict) -> Session:
    """
    Takes the full AIRE pipeline JSON payload and saves it
    across all four tables in a single transaction.

    Usage:
        session_record = save_session_payload(payload)
        db.session.add(session_record)
        db.session.commit()
    """
    session_data = payload.get('session', {})
    reply = session_data.get('reply', {})
    questions = payload.get('questions', [])
    amb_type_of_qn = payload.get('ambiguities', [])
    answers = payload.get('answers', [])

    # Parse DETAILED_PREDICTIONS JSON string
    detailed = {}
    if 'DETAILED_PREDICTIONS' in reply:
        try:
            detailed = json.loads(reply['DETAILED_PREDICTIONS'])
        except (json.JSONDecodeError, TypeError):
            detailed = {}

    # ── 1. Create Session record ───────────────────────────────────────────────
    session_record = Session(
        token=session_data.get('token', 'UNKNOWN'),
        status=session_data.get('status', 'clarify'),
        domain=reply.get('DOMAIN'),
        ambiguity_count=session_data.get('ambiguous', 0),
        raw_paragraph=' '.join(
            detailed.get('Raw_requirement', {}).values()
        ) if detailed else None,
    )
    db.session.add(session_record)
    db.session.flush()  # get session_record.id before committing

    # ── 2. Create Sentence records ─────────────────────────────────────────────
    ambiguity_types = [
        'SemanticAmbiguity', 'ScopeAmbiguity',
        'ActorAmbiguity', 'ProcessExecutionAmbiguity'
    ]

    sentence_records = {}
    raw_reqs = detailed.get('Raw_requirement', {})
    req_types = detailed.get('requirement_type', {})
    has_amb = detailed.get('HasAmbiguity', {})
    conf_scores = detailed.get('confidance_scores', {})

    for idx_str, raw_text in raw_reqs.items():
        sentence_record = Sentence(
            session_id=session_record.token,
            sentence_index=int(idx_str),
            raw_text=raw_text,
            requirement_type=req_types.get(idx_str),
            confidence_score=conf_scores.get(idx_str),
            has_ambiguity=bool(has_amb.get(idx_str, 0)),
        )
        db.session.add(sentence_record)
        db.session.flush()
        sentence_records[idx_str] = sentence_record

    # ── 3. Create AmbiguityResult records ─────────────────────────────────────
    for amb_type in ambiguity_types:
        amb_data = detailed.get(amb_type, {})
        for idx_str, detected_val in amb_data.items():
            sentence_rec = sentence_records.get(idx_str)
            if sentence_rec:
                amb_result = AmbiguityResult(
                    session_id=session_record.token,
                    sentence_id=sentence_rec.id,
                    ambiguity_type=amb_type,
                    detected=bool(detected_val),
                )
                db.session.add(amb_result)

    # ── 4. Create Clarification records ───────────────────────────────────────

    # Distribute questions into types based on detected ambiguities

    for i in range(len(questions)):
        answer_val = answers[i] if i < len(answers) else None
        print("answer_val:", answer_val, "answers[i]:", answers[i])
        is_answered = (answer_val is not None and answer_val != "")
        clarification = Clarification(
            session_id=session_record.token,
            ambiguity_type=amb_type_of_qn[i],
            question=questions[i],
            answer=answer_val if is_answered else None,
            answered=is_answered,
            answered_at=datetime.utcnow() if is_answered else None,
        )
        db.session.add(clarification)
    return session_record
