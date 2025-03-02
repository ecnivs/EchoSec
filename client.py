from llm_handler import *

llm = get_llm()

while True:
    query = input("-> ")
    response = []
    for chunk in llm.get_response(query):
        if chunk.strip():
            print(chunk)
            response.append(chunk)
