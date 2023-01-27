from sklearn.feature_extraction.text import CountVectorizer
import re

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
        print("Matching:", eval(rewrite_query(query))) # Eval runs the string as a Python command
        hits_matrix = eval(rewrite_query(query))
        hits_list = list(hits_matrix.nonzero()[1])
        for doc_idx in hits_list:
            print("Matching doc:", documents[doc_idx])
        print()
    except KeyError: # This activates if there's a KeyError caused by one or more tokens in the query not being present in the given documents
        query_list = rewrite_query(query).split("|") # Makes a list of each term requested in a query containing an "OR" statement (so if only one of the terms requested has no matches, we will still be getting results for the terms that do have matches 
        for i in query_list:
            iname = re.sub(r"sparse_td_matrix\[t2i\[\"(.*)\"\]\].todense\(\)", r"\1", i) #extract item name for later use
            try:
                print("Matching '" + iname + "' :", eval(i))
                hits_matrix = eval(i)
                hits_list = list(hits_matrix.nonzero()[1])
                for doc_idx in hits_list:
                    print("Matching doc for '" + iname + "' :", documents[doc_idx])
                print()
            except KeyError:
                print("No match: '" + iname + "' cannot be found in any of the given documents")


# Program that asks the user for a search query, program quits when an empty string is entered

print("Search engine starts...\n")
print("*** The query should be of the form of the following examples: ***\n")

print("    example AND NOT nothing")
print("    NOT example OR great")
print("    ( NOT example OR great ) AND nothing\n")

print("*** Operators AND, OR, NOT need to be written in ALLCAPS ***\n")

while True:
    user_query = str(input("Enter your query (empty string quits program): \n"))
    if user_query == "":
        break
    else:
        test_query(f"{user_query}")
