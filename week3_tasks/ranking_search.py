from sklearn.feature_extraction.text import CountVectorizer
import re
import numpy as np

# read articles from file
with open('../data/enwiki-20181001-corpus.1000-articles.txt', encoding='utf8') as f:
    content = f.read()

# split by closing article tag, and then remove opening tag
# save document titles in separate array
documents = content.strip().split('</article>')
p = re.compile('^\s*<article\s+name="(.*?)"\s*>\s*')
documents_titles = [p.match(document).group(1) for document in documents if document and p.match(document)]
documents = [re.sub(p, "", document) for document in documents if document and p.match(document)]

def boolean_query_matrix(t):
    """
    Checks if the term is present in any of the documents.
    If present, returns the hits matrix, and if not, an empty row to be used in calculations
    """
    return sparse_td_matrix[t2i[t]].todense() if t in t2i.keys() else np.array([[0] * len(documents)])

def boolean_rewrite_token(t):
    return d.get(t, 'boolean_query_matrix("{:s}")'.format(t)) 

def boolean_rewrite_query(query): # rewrite every token in the query
    return " ".join(boolean_rewrite_token(t) for t in query.split())

def boolean_test_query(query):
    print("Query: '" + query + "'")
    if np.all(eval(boolean_rewrite_query(query)) == 0):
        print("No matches: there are no documents matching the query '" + query + "'")
    else:
        print("Matching:", eval(boolean_rewrite_query(query))) # Eval runs the string as a Python command
        hits_matrix = eval(boolean_rewrite_query(query))
        hits_list = list(hits_matrix.nonzero()[1])
        print(str(len(hits_list)) + " matching documents in total.")
        # Here we print only the first 10 matching documents and only the first 1000 characters from the documents:
        doc_number = 1
        for doc_idx in hits_list[:10]:
            print(f"\nMatching doc #{doc_number}: \n")
            if (len(documents[doc_idx]) > 1000):
                print(documents[doc_idx][:1000] + "...")
            else:
                print(documents[doc_idx])
            doc_number += 1


# Program that asks the user for a search query, program quits when an empty string is entered
def boolean_search():
    cv = CountVectorizer(lowercase=True, binary=True, stop_words=None, token_pattern=r'(?u)\b\w+\b')
    sparse_matrix = cv.fit_transform(documents)
    sparse_td_matrix = sparse_matrix.T.tocsr()

    # Operators AND, OR, NOT become &, |, 1 -
    # Parentheses are left untouched
    # Everything else is interpreted as a term and fed through td_matrix[t2i["..."]]
    global d
    d = {"AND": "&",
         "OR": "|",
         "NOT": "1 -",
         "(": "(", ")": ")"}          # operator replacements

    # For the operators we'll only use AND, OR, NOT in ALLCAPS in order to avoid conflict with the corresponding words in lowercase letters in the documents
    global t2i
    t2i = cv.vocabulary_  # shorter notation: t2i = term-to-index

    
    print("\n*** The query should be of the form of the following examples: ***\n")

    print("    you AND i")
    print("    example AND NOT nothing")
    print("    NOT example OR great")
    print("    ( NOT example OR great ) AND nothing")

    print("\n*** Operators AND, OR, NOT need to be written in ALLCAPS, search words in lowercase. ***")


    while True:
        user_query = str(input("\nEnter your query (empty string quits program): \n"))
        if user_query == "":
            break
        else:
            try:
                print("\nResults:")
                boolean_test_query(f"{user_query}")
            except SyntaxError:
                print("\n*** The input was erroneous, cannot show all results.\nMake sure the operators are typed in ALLCAPS. ***\n")
                                        
print("Search engine starts...")
boolean_search()
