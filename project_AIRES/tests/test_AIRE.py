import spacy
from spacy import displacy
import pandas as pd
import numpy as np
import json

nlp = spacy.load('en_core_web_md')

with open('AIRE_project/tests/vocab.json', 'r') as f:
    greet = json.load(f)

prompt = nlp("hiya")
types_of_greets = np.array([x for x in greet['greetings'].keys()])
greets_list = []
for greet_type in types_of_greets:
    greets_list.extend(greet['greetings'][greet_type]['words'])
greets_list = list(nlp.pipe(greets_list))  # storing each of the word as doc object
greets_list_vector = np.array([
    prompt.similarity(doc) if doc.has_vector and prompt.has_vector else 0.0 for doc in greets_list
])
response = ''
for x, y in zip(greets_list, greets_list_vector):
    if max(greets_list_vector) == y:
        word = x.text
        for greet_type in types_of_greets:
            if word in greet['greetings'][greet_type]['words']:
                response = greet["respons"]["common"][greet_type]
print('AIRE:', response)
