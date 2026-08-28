from AIRE import app
from AIRE.models import AmbiguityResult, Clarification, Sentence, Session
with app.app_context():
    clarification_rows = Clarification.query.filter_by(session_id="5153241C").all()
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
    for x, y, z in zip(ambiguities, answers, questions):
        print(x, "|||", y, "|||", z)
