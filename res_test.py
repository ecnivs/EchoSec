from llm_handler import LlmHandler
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from collections import Counter
from settings import *

stemmer = PorterStemmer()

def extract_key_phrases(query):
    """Extracts key phrases from the query using stemming and removes stop words."""
    stop_words = set(stopwords.words('english'))
    words = re.sub(r'[^a-zA-Z\s]', '', query.lower()).split()
    word_counts = Counter([stemmer.stem(word) for word in words if word not in stop_words])
    result = list(word_counts.keys())
    if not result:
        return query.split()
    if result and result[0] in EXCLUDED_PREFIXES:
        result.pop(0)
    return result

llm = LlmHandler(SIM_PROMPT)

while True:
    query = input("Query: ")

    intent_name = '.'.join(extract_key_phrases(query))
    print(intent_name)
    continue
    response = []
    for chunk in llm.get_response(query):
        if chunk.strip():
            print(chunk)
