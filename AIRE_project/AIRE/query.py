from AIRE import app
from AIRE.models import AmbiguityResult, Clarification, Sentence, Session
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
