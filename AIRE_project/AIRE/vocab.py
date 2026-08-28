
from collections import Counter
import spacy
import pandas as pd
import numpy as np
import json
import joblib
import scipy.sparse as sp


with open('AIRE_project/AIRE/vocab.json', 'r') as f:  # change vocab.json to vocab1.json imple
    Vocab = json.load(f)
with open("AIRE_project/AIRE/edge_values.json", 'r') as f:
    edge_values = json.load(f)
nlp = spacy.load('en_core_web_md')


def greet(text):
    prompt = nlp(text)
    type_of_greet = ''
    types_of_greets = np.array([x for x in Vocab['greetings'].keys()])
    greets_list = []
    for greet_type in types_of_greets:
        greets_list.extend(Vocab['greetings'][greet_type]['words'])
    greets_list = list(nlp.pipe(greets_list))  # storing each of the word as doc object
    greets_list_vector = np.array([
        prompt.similarity(doc) if doc.has_vector and prompt.has_vector else 0.0 for doc in greets_list
    ])
    response = ''
    for x, y in zip(greets_list, greets_list_vector):
        if max(greets_list_vector) == y:
            word = x.text
            for greet_type in types_of_greets:
                if word in Vocab['greetings'][greet_type]['words']:
                    type_of_greet = greet_type
                    response = Vocab["respons"]["common"][greet_type]
    return {
        "max_similarity_value": float(max(greets_list_vector)),
        "similar_greet_type": str(type_of_greet),
        "response": response
    }


def brain():
    import os
    # 1. Suppress TensorFlow C++ logging level (0 = ALL, 1 = Filter INFO, 2 = Filter WARNING, 3 = Filter ERROR)
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    # 2. Disable oneDNN floating-point warning
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
    import keras  # noqa
    BA_MODEL = joblib.load('AIRE_project/AIRE/ba_brain_model.pkl')
    VOCAB_MODEL = joblib.load('AIRE_project/AIRE/ba_brain_tfidf.pkl')
    AA_MODEL = keras.models.load_model("AIRE_project/AIRE/multitask_ambiguity_model.keras")
    return BA_MODEL, VOCAB_MODEL, AA_MODEL


nlp = spacy.load('en_core_web_md')

with open('AIRE_project/AIRE/requirement_classifier.json', 'r') as f:
    requirement_classifier_df = json.load(f)
requirement_classifier_df = pd.DataFrame(requirement_classifier_df)

# Global Functions

# REQUIREMENT CLASSIFIER FUNCTIONS ------------------------------


def sententizer(text):
    doc = nlp(text.lower())
    preprocessed = []
    sents = []
    for sent in doc.sents:
        filtered = []
        sents.append(sent.text)
        for token in sent:
            if token.is_stop or token.is_punct:
                continue
            filtered.append(token.lemma_)
        preprocessed.append(" ".join(filtered))
    return np.array(preprocessed), sents


def input_text(sent):
    BA_MODEL, VOCAB_MODEL, AA_MODEL = brain()
    # Step 1 — preprocess and transform (NOT fit_transform)
    x_tfidf = VOCAB_MODEL.transform([sent])

    # Step 2 — domain keyword features (no loop, single sentence)
    x_keywords = np.array([domain_keyword_features(sent)])
    x_keywords_sparse = sp.csr_matrix(x_keywords)

    # Step 3 — combine
    return sp.hstack([x_tfidf, x_keywords_sparse])


def domain_keyword_features(text):
    with open('AIRE_project/AIRE/domain_vocab.json', 'r') as f:
        domain_vocab = json.load(f)
    domain_vocab = pd.DataFrame(domain_vocab)
    text_lower = text.lower()
    features = []

    for category, words in domain_vocab.loc['BLEND_INFLUENCERS'].items():
        # Count how many keywords from each category appear
        count = sum(1 for w in words if w in text_lower)
        features.append(count)  # count, not just binary 0/1

    return features


def get_confidence_fast(text):
    BA_MODEL, VOCAB_MODEL, AA_MODEL = brain()
    try:
        text = str(text)
        # TF-IDF transform only — no spaCy
        x_tfidf = VOCAB_MODEL.transform([text])
        x_keywords = sp.csr_matrix(np.array([domain_keyword_features(text)]))
        x_combined = sp.hstack([x_tfidf, x_keywords])
        # Get confidence
        proba = BA_MODEL.predict_proba(x_combined)[0]
        return round(max(proba), 4)
    except Exception as e:
        print(f"Error: {e}")
        return None

# REQUIREMENT CLASSIFIER FUNCTIONS ------------------------------

# AMBIGUITY ANALYZER FUNCTIONS ----------------------------------


def wordEmbedding(sents):
    from sentence_transformers import SentenceTransformer

    # Load pre-trained model (downloads once, ~80MB)
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    return np.array([embedder.encode(x, show_progress_bar=False) for x in sents])


domain_dict = {'Telecommunications': 0,
               'Finance': 1,
               'E-commerce': 2,
               'Healthcare': 3,
               'Manufacturing': 4}


def decode_domain(df, domain_dict):
    reverse_domain_mapping = {}
    for x, y in domain_dict.items():
        reverse_domain_mapping[y] = x
    df.Domain = df.Domain.replace(reverse_domain_mapping)
    return df


def convert_numpy_types(data):
    if isinstance(data, dict):
        return {key: convert_numpy_types(val) for key, val in data.items()}
    elif isinstance(data, list):
        return [convert_numpy_types(item) for item in data]
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, (np.float64, np.float32, np.float16)):
        return float(data)
    elif isinstance(data, (np.int64, np.int32, np.int16)):
        return int(data)
    return data


#  High-Lavel Functions-----------------------------------------------------------


def base_requirement_table(RAW_REQ):  # GENERATE A PANDAS TABLE --> return : a DataFrame
    import tensorflow as tf  # noqa
    BA_MODEL, VOCAB_MODEL, AA_MODEL = brain()
    # Preproecessing and sentenctizer Layer
    preprocessed, raw = sententizer(RAW_REQ)
    # RE Type classification Layer
    RE_classes = np.array([BA_MODEL.predict(input_text(x))[0] for x in preprocessed])
    confidance_scores = np.array([get_confidence_fast(x) for x in preprocessed])
    # Ambiguity Type classification Layer
    Vectors = tf.convert_to_tensor(wordEmbedding(preprocessed), dtype=tf.float32)
    preds = AA_MODEL.predict(Vectors)

    # Apply your optimal decision thresholds AA_MODEL predictions
    has_ambiguity_preds = (preds[0] >= edge_values["has_ambiguity_preds"][0]).astype(int)
    domain_preds = np.array([np.argmax(i) for i in preds[1]])
    SemanticAmbiguity_pred = (preds[2][:, 0] >= edge_values["SemanticAmbiguity_pred"][0]).astype(int)
    ScopeAmbiguity_pred = (preds[2][:, 1] >= edge_values["ScopeAmbiguity_pred"][0]).astype(int)
    ActorAmbiguity_pred = (preds[2][:, 2] >= edge_values["ActorAmbiguity_pred"][0]).astype(int)
    process_preds = (preds[3] >= edge_values["process_preds"][0]).astype(int)
    # Combine all predictions into one DataFrame
    results_df = pd.DataFrame({
        'Raw_requirement': raw,
        'HasAmbiguity': has_ambiguity_preds.flatten(),
        'Domain': domain_preds,
        'requirement_type': RE_classes,
        'SemanticAmbiguity': SemanticAmbiguity_pred,
        'ScopeAmbiguity': ScopeAmbiguity_pred,
        'ActorAmbiguity': ActorAmbiguity_pred,
        'ProcessExecutionAmbiguity': process_preds.flatten(),
        'confidance_scores': confidance_scores
    })

    # Display or save results
    # results_df.to_csv("test_predictions_results.csv", index=False)
    decode_domain(results_df, domain_dict)
    return results_df


#  High-Lavel Functions-----------------------------------------------------------
def response_constructor(results_df):  # Convert the prediction into a python Dictionary ---> Return : a Dictionary
    results_df.requirement_type.unique()
    c = Counter(results_df.Domain.values)
    domain = c.most_common()[0][0]

    text = []
    requirements = []
    for x in range(len(results_df)):
        # print(results_df.iloc[x])
        item = dict({
            'id': x,
            'sentence': results_df.iloc[x]['Raw_requirement'],
            'requirement_type': results_df.iloc[x]['requirement_type'],
            'requiremnt_type_confidance': results_df.iloc[x]['confidance_scores']
        })
        text.append(item)

    item1 = {}
    for req in results_df.requirement_type.unique():
        overall_ambiguity = (results_df.HasAmbiguity == 1)
        item1[req] = dict({
            'NumbersOfSentances': len(results_df.loc[(results_df.requirement_type == req) & overall_ambiguity]),
            'overallAmbiguity': results_df.loc[(results_df.requirement_type == req) & overall_ambiguity].index.values,
            'SemanticAmbiguity': results_df.loc[(results_df.requirement_type == req) & (results_df.SemanticAmbiguity == 1) & overall_ambiguity].index.values,
            'ScopeAmbiguity': results_df.loc[(results_df.requirement_type == req) & (results_df.ScopeAmbiguity == 1) & overall_ambiguity].index.values,
            'ActorAmbiguity': results_df.loc[(results_df.requirement_type == req) & (results_df.ActorAmbiguity == 1) & overall_ambiguity].index.values,
        })
    requirements.append(item1)
    # text
    requirements[0]

    final_dict = dict({
        'domain': domain,
        'total_ambiguity': len(results_df.loc[results_df.HasAmbiguity == 1]),
        'text': text,
        'requirements': requirements[0]
    })
    return convert_numpy_types(final_dict), results_df.to_json()

#  High-Lavel Functions-----------------------------------------------------------


def bot_response(final_dict, detailedPred):  # Collecting all of the ambiguities type in the paragraph ---> return: a Final response
    detected_requirement_types = final_dict['requirements'].keys()
    detected_ambiguities = set()
    initial_prompts = set()
    senteces_ambiguity = {}
    for requirement_type in detected_requirement_types:
        for i, ambiguity_type in enumerate(list(final_dict['requirements'][requirement_type].keys())[2:]):
            if len(final_dict['requirements'][requirement_type][ambiguity_type]) != 0:
                detected_ambiguities.add(ambiguity_type)
                senteces_ambiguity[ambiguity_type] = []

    for requirement_type in detected_requirement_types:
        for ambiguity in list(detected_ambiguities):
            initial_prompts.add(Vocab["respons"]["AMBIGUITY_INITIAL_PROMPTS"][ambiguity])
            senteces_ambiguity[ambiguity].extend(final_dict['requirements'][requirement_type][ambiguity])

    string = ""
    for i, x in enumerate(initial_prompts):
        if i != 0:
            sent = x.replace("Your requirement", "It")
        else:
            sent = x
        string += sent+" "

    keyQuestions = ""
    grouped_by_ambiguity = dict()
    for ambiguity in senteces_ambiguity.keys():
        # print(final_dict['text'][senteces_ambiguity[x]]['sentence'])
        probs = " ".join([final_dict['text'][ID]['sentence'] for ID in senteces_ambiguity[ambiguity]])
        grouped_by_ambiguity[ambiguity] = probs
        qna = ""
        for i, question in enumerate(Vocab["respons"]["AMBIGUITY_CLARIFICATION_QUESTIONS"][ambiguity]):
            qna += f"\n({i+1}) {question}"
        corps = f'''
        -----------------------------------------------------------------------------
        {probs}
        -----------------------------------------------------------------------------
        In here actually,{qna}
        '''
        keyQuestions += corps

    final_response = f'''Detected Ambiguities(Interactive Labels) : {[x for x in list(detected_ambiguities)]}

    {string} 

    Specifically, You have mentioned,
    {keyQuestions}

    '''

    final_res_dict = dict({
        'DOMAIN': final_dict['domain'],
        'DETECTED_AMBIGUITES': [x for x in list(detected_ambiguities)],
        'DESCRIPTION': string,
        'GROUPED_BY_AMBIGUITY': grouped_by_ambiguity,
        'DETAILED_PREDICTIONS': detailedPred
    })
    return final_response, final_res_dict
#  High-Lavel Functions-----------------------------------------------------------


# USAGE_TEST
# # Input Pipeline ------------------------------------------------
# RAW_REQ = "We operate an online marketplace with many sellers. Customers should be able to find products and place orders, while sellers need to manage the products they offer and update their orders. Administrators should handle problems reported by customers and monitor the performance of sellers. The company also wants reports to understand sales activity."
# # Input Pipeline ------------------------------------------------

# results_df = base_requirement_table(RAW_REQ)
# final_dict = response_constructor(results_df)

# print(bot_response(final_dict))
