"""
LABEL MAPPER
------------
Maps ML model label outputs to human-readable response sentences
using a plain Python dictionary, as specified in the project context.

Example:
    Dataset column value = 3
    Dictionary entry: {"3": "Please provide a specific target date."}
"""
import random
from AIRE.vocab import Vocab, greet

keys = list(Vocab["respons"]["question"].keys())  # Question Keys


def map_label_to_response(label, direct_res):
    """Look up the clarifying sentence for a given label."""
    print("LABEL(label_mapper) : ", label)
    if label == 'greeting':
        return direct_res
    elif label in keys:
        return f'''{direct_res}
                   \n{Vocab["respons"]["question"].get(str(label), direct_res)}'''
    else:
        return Vocab["respons"]["question"].get(str(label), direct_res)
