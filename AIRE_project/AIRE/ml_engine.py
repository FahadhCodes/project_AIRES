"""
ML ENGINE (stub)
----------------
This is a placeholder for Model 1 (BA Brain) ambiguity/ambiguous scoring.
Replace classify_requirement() with a real scikit-learn pipeline
(e.g. TF-IDF + SVM or Naive Bayes) trained on your merged DataFrame.

Contract this function must honor (so app.py never needs to change):
    Input  : requirement_text (str)
    Output : {
        "ambiguous": float (0.0 - 1.0),
        "label": str (matches a key in label_mapper.LABEL_MAP)
    }
"""
import random
from AIRE.vocab import greet, Vocab, base_requirement_table, response_constructor, bot_response
import json
import spacy


nlp = spacy.load('en_core_web_md')


def classify_requirement(requirement_text: str) -> dict:
    """
    TEMPORARY STUB.
    Currently returns a random label + ambiguous so the
    Flask <-> UI <-> routing logic can be tested end-to-end
    before the real scikit-learn model is wired in.
    """
    data = greet(requirement_text)
    ambiguous = round(random.uniform(0.60, 0.99), 2)
    # label = random.choice(list(QUES))
    doc = nlp(requirement_text)
    keys = list(Vocab["respons"]["question"].keys())  # Question Keys

    if data['max_similarity_value'] > 0.75 and len(doc) < 7:
        ambiguous = 0
        label = "greeting"
        res = data['response']
        condition_id = 'A'
    elif data['max_similarity_value'] > 0.75 and len(doc) > 7:
        label = "question"
        results_df = base_requirement_table(requirement_text)
        final_dict = response_constructor(results_df)
        final_res, final_res_dict = bot_response(final_dict)
        ambiguous = final_dict['total_ambiguity']
        res = final_res_dict
        condition_id = 'B'
    else:
        label = "question"
        results_df = base_requirement_table(requirement_text)
        final_dict = response_constructor(results_df)
        final_res, final_res_dict = bot_response(final_dict)
        ambiguous = final_dict['total_ambiguity']
        res = final_res_dict
        condition_id = 'C'
    # ----------------------------------------------------------------
    print(f'''DEBUGGING: 
                      Conversation Direction : {label} 
                      Confidance Score of requirenment :{ambiguous}
                      Similarity Value :{data['max_similarity_value']}
                      Condition ID :{condition_id}
    ''')
    # ----------------------------------------------------------------
    return {
        "ambiguous": ambiguous,
        "label": label,
        "response": res,
    }
