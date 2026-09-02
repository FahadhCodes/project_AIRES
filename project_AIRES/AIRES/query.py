from AIRES import app, db
from AIRES.models import AmbiguityResult, Clarification, Sentence, Session, Company, User
import json

with app.app_context():

    def reconstruct_payload(token: str) -> dict:
        """
        Reconstruct the full AIRE payload JSON from SQLite
        for a given session token.
        """

        # ── 1. Query all four tables ───────────────────────────────────────────────
        session_row = Session.query.filter_by(token=token).first_or_404()
        sentence_rows = Sentence.query.filter_by(session_id=token)\
            .order_by(Sentence.sentence_index).all()
        ambiguity_rows = AmbiguityResult.query.filter_by(session_id=token).all()
        clarification_rows = Clarification.query.filter_by(session_id=token).all()

        # ── 2. Rebuild session block ───────────────────────────────────────────────
        reply = {}
        session = {}

        session["status"] = session_row.status
        session["token"] = session_row.token
        # session["submitted_at"] = session_row.submitted_at
        session["label"] = "question"
        session["ambiguous"] = session_row.ambiguity_count

        # ── 3. Rebuild reply.DOMAIN ────────────────────────────────────────────────
        reply["DOMAIN"] = session_row.domain

        # ── 4. Rebuild reply.DETECTED_AMBIGUITES ──────────────────────────────────
        # Only ambiguity types where detected=True, deduplicated, ordered
        AMBIGUITY_ORDER = [
            "ActorAmbiguity",
            "ScopeAmbiguity",
            "SemanticAmbiguity",
            "ProcessExecutionAmbiguity"
        ]
        detected_set = set(
            r.ambiguity_type
            for r in ambiguity_rows
            if r.detected
        )
        # Preserve order defined in AMBIGUITY_ORDER
        reply["DETECTED_AMBIGUITES"] = [
            t for t in AMBIGUITY_ORDER if t in detected_set
        ]

        # ── 5. Rebuild reply.DESCRIPTION ──────────────────────────────────────────
        # Reconstruct from detected ambiguity types using vocab descriptions
        AMBIGUITY_INITIAL_PROMPTS = {
            "SemanticAmbiguity": "It contains unclear or subjective terms that may be understood differently.",

            "ScopeAmbiguity": "It has unclear boundaries, so it is not clear exactly what is included.",

            "ActorAmbiguity": "It does not clearly identify who should perform this action.",

            "AcceptanceAmbiguity": "It does not clearly explain how we can decide whether the result is successful.",

            "DependencyAmbiguity": "It depends on another person, process, system, or event that is not clearly specified.",

            "PriorityAmbiguity": "It does not clearly indicate how important or urgent it is.",

            "TechnicalAmbiguity": "It mentions a technical operation without clearly specifying what is expected."
        }
        description_parts = []
        for i, amb_type in enumerate(reply["DETECTED_AMBIGUITES"]):
            prompt = AMBIGUITY_INITIAL_PROMPTS.get(amb_type, "")
            # First sentence keeps "Your requirement", rest use "It"
            if i == 0:
                description_parts.append(prompt)
            else:
                description_parts.append(prompt.replace("Your requirement", "It"))
        reply["DESCRIPTION"] = " ".join(description_parts)

        # ── 6. Rebuild reply.GROUPED_BY_AMBIGUITY ─────────────────────────────────
        # For each ambiguity type — collect sentence texts where that type was detected
        grouped = {}
        for amb_type in reply["DETECTED_AMBIGUITES"]:
            # Get sentence IDs where this ambiguity type is detected
            affected_sentence_ids = set(
                r.sentence_id
                for r in ambiguity_rows
                if r.ambiguity_type == amb_type and r.detected
            )
            # Get sentence texts for those IDs ordered by index
            affected_texts = [
                s.raw_text
                for s in sentence_rows
                if s.id in affected_sentence_ids
            ]
            if affected_texts:
                grouped[amb_type] = " ".join(affected_texts)

        reply["GROUPED_BY_AMBIGUITY"] = grouped

        # ── 7. Rebuild reply.DETAILED_PREDICTIONS ─────────────────────────────────
        # Reconstruct the nested dict that was originally serialised as a JSON string
        amb_types_all = [
            "SemanticAmbiguity",
            "ScopeAmbiguity",
            "ActorAmbiguity",
            "ProcessExecutionAmbiguity"
        ]

        detailed = {
            "Raw_requirement": {},
            "HasAmbiguity": {},
            "Domain": {},
            "requirement_type": {},
            "SemanticAmbiguity": {},
            "ScopeAmbiguity": {},
            "ActorAmbiguity": {},
            "ProcessExecutionAmbiguity": {},
            "confidance_scores": {},
        }

        for s in sentence_rows:
            idx = str(s.sentence_index)

            detailed["Raw_requirement"][idx] = s.raw_text
            detailed["HasAmbiguity"][idx] = 1 if s.has_ambiguity else 0
            detailed["Domain"][idx] = session_row.domain  # session-level domain
            detailed["requirement_type"][idx] = s.requirement_type or ""
            detailed["confidance_scores"][idx] = s.confidence_score or 0.0

            # Fill ambiguity type columns per sentence
            for amb_type in amb_types_all:
                # Find the ambiguity result for this sentence + type
                match = next(
                    (r for r in ambiguity_rows
                     if r.sentence_id == s.id and r.ambiguity_type == amb_type),
                    None
                )
                detailed[amb_type][idx] = 1 if (match and match.detected) else 0

        # Serialise back to JSON string — matches original payload format
        reply["DETAILED_PREDICTIONS"] = detailed

        # ── 8. Rebuild questions and answers ──────────────────────────────────────
        # Order clarifications: Actor → Scope → Semantic → Process
        ambi = set()
        questions = []
        answers = []
        ambiguities = []
        for x in clarification_rows:
            ambi.add(x.ambiguity_type)
            # print(x.ambiguity_type,"|||",x.question)
        for y in sorted(ambi):
            for x in clarification_rows:
                if y == x.ambiguity_type:
                    questions.append(x.question)
                    answers.append(x.answer)
                    ambiguities.append(x.ambiguity_type)

        # for x, y, z in zip(ambiguities, answers, questions):
        #     print(x, "|||", y, "|||", z)

        # ── 9. Assemble final payload ──────────────────────────────────────────────
        session["reply"] = reply

        payload = {
            "questions": questions,
            "answers": answers,
            "ambiguities": ambiguities,
            "session": session,
        }

        return payload

    def reconstruct_company_payload(company_id: int) -> dict:
        """Build an aggregated dashboard payload for one company."""
        company = Company.query.filter_by(id=company_id).first_or_404()
        session_tokens = {
            company.session_id,
            *(
                session_id
                for (session_id,) in db.session.query(User.session_id)
                .filter(User.company_id == company.id)
                .distinct()
                .all()
            ),
        }
        sessions = (
            Session.query.filter(Session.token.in_(session_tokens))
            .order_by(Session.submitted_at.desc())
            .all()
        )

        ambiguity_order = [
            "ActorAmbiguity",
            "ScopeAmbiguity",
            "SemanticAmbiguity",
            "ProcessExecutionAmbiguity",
        ]
        ambiguity_types = [
            "SemanticAmbiguity",
            "ScopeAmbiguity",
            "ActorAmbiguity",
            "ProcessExecutionAmbiguity",
        ]
        detailed = {
            "Raw_requirement": {},
            "HasAmbiguity": {},
            "Domain": {},
            "requirement_type": {},
            "confidance_scores": {},
            "SessionToken": {},
            **{amb_type: {} for amb_type in ambiguity_types},
        }
        questions, answers, ambiguities = [], [], []
        grouped = {}
        detected_types = set()
        total_ambiguities = 0
        session_summaries = []
        aggregate_index = 0

        for session_row in sessions:
            sentences = Sentence.query.filter_by(session_id=session_row.token).order_by(
                Sentence.sentence_index
            ).all()
            ambiguity_rows = AmbiguityResult.query.filter_by(session_id=session_row.token).all()
            ambiguity_by_sentence = {}
            for row in ambiguity_rows:
                ambiguity_by_sentence.setdefault(row.sentence_id, set()).add(row.ambiguity_type)
                if row.detected:
                    detected_types.add(row.ambiguity_type)
                    total_ambiguities += 1

            session_ambiguous = sum(1 for sentence in sentences if sentence.has_ambiguity)
            session_summaries.append({
                "token": session_row.token,
                "domain": session_row.domain,
                "status": session_row.status,
                "sentence_count": len(sentences),
                "ambiguity_count": session_ambiguous,
            })

            for sentence in sentences:
                idx = str(aggregate_index)
                sentence_ambiguities = ambiguity_by_sentence.get(sentence.id, set())
                detailed["Raw_requirement"][idx] = sentence.raw_text
                detailed["HasAmbiguity"][idx] = int(sentence.has_ambiguity)
                detailed["Domain"][idx] = session_row.domain
                detailed["requirement_type"][idx] = sentence.requirement_type or ""
                detailed["confidance_scores"][idx] = sentence.confidence_score or 0.0
                detailed["SessionToken"][idx] = session_row.token
                for amb_type in ambiguity_types:
                    detected = amb_type in sentence_ambiguities
                    detailed[amb_type][idx] = int(detected)
                    if detected:
                        grouped.setdefault(amb_type, []).append(sentence.raw_text)
                aggregate_index += 1

            clarifications = Clarification.query.filter_by(session_id=session_row.token).order_by(
                Clarification.id
            ).all()
            for clarification in clarifications:
                questions.append(clarification.question)
                answers.append(clarification.answer)
                ambiguities.append(clarification.ambiguity_type)

        detected_ambiguities = [amb_type for amb_type in ambiguity_order if amb_type in detected_types]
        domains = list(dict.fromkeys(summary["domain"] for summary in session_summaries if summary["domain"]))
        status = "resolved" if sessions and all(
            item["status"] == "resolved" for item in session_summaries) else "clarify"

        return {
            "company": {
                "id": company.id,
                "company_name": company.company_name,
                "industry": company.industry,
                "company_size": company.company_size,
                "website_url": company.website_url,
                "billing_email": company.billing_email,
            },
            "sessions": session_summaries,
            "questions": questions,
            "answers": answers,
            "ambiguities": ambiguities,
            "session": {
                "token": str(company.id),
                "status": status,
                "ambiguous": sum(item["ambiguity_count"] for item in session_summaries),
                "reply": {
                    "DOMAIN": ", ".join(domains) or "Not detected",
                    "DETECTED_AMBIGUITES": detected_ambiguities,
                    "DESCRIPTION": f"{total_ambiguities} ambiguity results across {len(sessions)} session(s).",
                    "GROUPED_BY_AMBIGUITY": {key: " ".join(value) for key, value in grouped.items()},
                    "DETAILED_PREDICTIONS": detailed,
                },
            },
        }

    def company_query(**company):
        token = (company.get("token") or "").strip()
        name = (company.get("name") or "").strip()

        # Prioritize searching by name when user is typing in the company input
        if name:
            companies = db.session.query(Company).filter(Company.company_name.ilike(f'%{name}%')).all()
        elif token:
            companies = db.session.query(Company).filter(Company.session_id == token).all()
        else:
            return {}

        if not companies:
            return {}

        return {
            "company_name": [c.company_name for c in companies],
            "industry": [c.industry for c in companies],
            "company_size": [c.company_size for c in companies],
            "website_url": [c.website_url for c in companies],
            "billing_email": [c.billing_email for c in companies],
        }

    def user_query(**user):
        token = (user.get("token") or "").strip()
        phone = (user.get("phone") or "").strip()

        # Prioritize searching by phone when user is typing in the phone input
        if phone:
            user_record = db.session.query(User).filter(User.phone_number.ilike(f'%{phone}%')).all()
        elif token:
            user_record = db.session.query(User).filter(User.session_id == token).all()
        else:
            return {}

        if not user_record:
            return {}

        return {
            "id": [u.id for u in user_record],
            "session_id": [u.session_id for u in user_record],
            "company_id": [u.company_id for u in user_record],
            "name": [u.name for u in user_record],
            "phone_number": [u.phone_number for u in user_record],
            "job_title": [u.job_title for u in user_record],
            "email": [u.email for u in user_record],
        }
