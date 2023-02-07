from flask import Flask, render_template, request
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import re
import numpy as np
import nltk
from nltk.stem.snowball import EnglishStemmer
from nltk.tokenize import word_tokenize
import shlex


#Initialize Flask instance
app = Flask(__name__)

example_data = [
    {'name': 'Cat sleeping on a bed', 'source': 'cat.jpg'},
    {'name': 'Misty forest', 'source': 'forest.jpg'},
    {'name': 'Bonfire burning', 'source': 'fire.jpg'},
    {'name': 'Old library', 'source': 'library.jpg'},
    {'name': 'Sliced orange', 'source': 'orange.jpg'}
]
# read articles from file
with open('../data/enwiki-20181001-corpus.1000-articles.txt', encoding='utf8') as f:
    content = f.read()

# split by closing article tag, and then remove opening tag
# save document titles in separate array
documents = content.strip().split('</article>')
p = re.compile('^\s*<article\s+name="(.*?)"\s*>\s*')
documents_titles = [p.match(document).group(1) for document in documents if document and p.match(document)]
documents = [re.sub(p, "", document) for document in documents if document and p.match(document)]

cv = CountVectorizer(lowercase=True, binary=True, stop_words=None, token_pattern=r'(?u)\b\w+\b', ngram_range=(1,3))
sparse_matrix = cv.fit_transform(documents)
sparse_td_matrix = sparse_matrix.T.tocsr()

d = {"AND": "&",
     "OR": "|",
     "NOT": "1 -",
     "(": "(", ")": ")"}          # operator replacements
# For the operators we'll only use AND, OR, NOT in ALLCAPS in order to avoid conflict with the corresponding words in lowercase letters in the documents

t2i = cv.vocabulary_  # shorter notation: t2i = term-to-index

def stem_que(query):
    return stemmer.stem(query) #returns stemmed query

def stem_doc():
    stem_single = []
    stem_docs = []
    for d in documents:
        d = d.lower()
        tok = word_tokenize(d)
        for t in tok:
            stem_single.append(" ".join(stemmer.stem(t)))
            stem_docs.append("".join(stem_single))
    return stem_docs #returns list of documents stemmed

def boolean_query_matrix(t):
    """
    Checks if the term is present in any of the documents.
    If present, returns the hits matrix, and if not, an empty row to be used in calculations
    """
    return sparse_td_matrix[t2i[t]].todense() if t in t2i.keys() else np.array([[0] * len(documents)])

def boolean_rewrite_token(t):
    return d.get(t, 'boolean_query_matrix("{:s}")'.format(t))

def boolean_rewrite_query(query): # rewrite every token in the query
    #if bool(re.search(r'\".+\"', query)) is False:
    #    query = stem_que(query)
    #else:
    #    query = re.sub('\"','', query)
    return " ".join(boolean_rewrite_token(t) for t in shlex.split(query))

def boolean_test_query(query):
    print("Query: '" + query + "'")

    matches = []
    if np.all(eval(boolean_rewrite_query(query)) == 0):
        return []
    else:
#        print("Matching:", eval(boolean_rewrite_query(query))) # Eval runs the string as a Python command
        hits_matrix = eval(boolean_rewrite_query(query))
        hits_list = list(hits_matrix.nonzero()[1])
#        print(str(len(hits_list)) + " matching documents in total.")
        for doc_idx in hits_list[:10]: #TODO don't restrict here, either add paging or at template
           matches.append({'name': documents_titles[doc_idx], 'text': documents[doc_idx][:1000]}) #TODO don't restrict here
    return matches


@app.route('/')
def hello_world():
   return "Hello, World!"

#Function search() is associated with the address base URL + "/search"
@app.route('/search')
def search():

    #Get query from URL variable
    query = request.args.get('query')


    #Initialize list of matches
    matches = []

    #If query exists (i.e. is not None)
    if query:
        #Look at each entry in the example data
        matches = boolean_test_query(f"{query}")

    #Render index.html with matches variable
    return render_template('index.html', matches=matches)