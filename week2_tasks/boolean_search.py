from sklearn.feature_extraction.text import CountVectorizer
import re
import numpy as np

# read articles from file
with open('enwiki-20181001-corpus.1000-articles.txt', encoding='utf8') as f:
    content = f.read()

# split by closing article tag, and then remove opening tag
# save document titles in separate array
documents = content.strip().split('</article>')
p = re.compile('^\s*<article\s+name="(.*?)"\s*>\s*')
documents_titles = [p.match(document).group(1) for document in documents if document and p.match(document)]
documents = [re.sub(p, "", document) for document in documents if document and p.match(document)]

cv = CountVectorizer(lowercase=True, binary=True, stop_words=None)
sparse_matrix = cv.fit_transform(documents)

sparse_td_matrix = sparse_matrix.T.tocsr()

# Operators and/AND, or/OR, not/NOT become &, |, 1 -
# Parentheses are left untouched
# Everything else is interpreted as a term and fed through td_matrix[t2i["..."]]

d = {"AND": "&",
     "OR": "|",
     "NOT": "1 -",
     "(": "(", ")": ")"}          # operator replacements

# For the operators we'll only use AND, OR, NOT in ALLCAPS in order to avoid conflict with the corresponding words in lowercase letters in the documents

t2i = cv.vocabulary_  # shorter notation: t2i = term-to-index

def rewrite_token(t):
    return d.get(t, 'sparse_td_matrix[t2i["{:s}"]].todense()'.format(t)) 

def rewrite_query(query): # rewrite every token in the query
    return " ".join(rewrite_token(t) for t in query.split())

def test_query(query):
    print("Query: '" + query + "'")
    print("Rewritten:", rewrite_query(query))
    try:
        if np.all(eval(rewrite_query(query)) == 0):
            print("No matches: there are no documents matching the query '" + query + "'")
        else:
            print("Matching:", eval(rewrite_query(query))) # Eval runs the string as a Python command
            hits_matrix = eval(rewrite_query(query))
            hits_list = list(hits_matrix.nonzero()[1])
            for doc_idx in hits_list:
                print("Matching doc:", documents[doc_idx])
            print()
    except KeyError: # This activates if there's a KeyError caused by one or more tokens in the query not being present in the given documents
        query_list = re.split("\||&", rewrite_query(query)) # Makes a list of each term requested in a query containing an "OR" or "AND" statement 
        for i in query_list:
            iname = re.sub(r"sparse_td_matrix\[t2i\[\"(.*)\"\]\].todense\(\)+", r"\1 ", i) #extract item name for later use
            try:
                print("Matching '" + iname + "' :", eval(i))
                hits_matrix = eval(i)
                hits_list = list(hits_matrix.nonzero()[1])
                for doc_idx in hits_list:
                    print("Matching doc for '" + iname + "' :", documents[doc_idx])
                print()
            except KeyError:
                print("No matches: there are no documents matching the word '" + iname + "'")


# Program that asks the user for a search query, program quits when an empty string is entered

print("Search engine starts...")
print("\n*** The query should be of the form of the following examples: ***\n")

print("    example AND NOT nothing")
print("    NOT example OR great")
print("    ( NOT example OR great ) AND nothing")

print("\n*** Operators AND, OR, NOT need to be written in ALLCAPS ***\n")


while True:
    user_query = str(input("Enter your query (empty string quits program): \n"))
    if user_query == "":
        break
    else:
        try:
            print("\nResults:")
            test_query(f"{user_query}")
        except SyntaxError:
            print("\n*** The input was erroneous, cannot show all results.\nMake sure the operators are typed in ALLCAPS. ***\n")
                                        
