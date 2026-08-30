from AIRE import app, db
from AIRE.models import AmbiguityResult, Clarification, Sentence, Session, Company
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
    # Matches "acme", "ACME", "AcMe", etc.
    companies = db.session.query(Company).filter(Company.company_name.ilike('%a%')).all()
    payLoad = {
        "company_name": [c.company_name for c in companies],
        "industry": [i.industry for i in companies],
        "company_size": [s.company_size for s in companies],
        "website_url": [u.website_url for u in companies],
        "billing_email": [b.billing_email for b in companies],
    }
    print(payLoad)
    # for i in companies:
