from flask import Flask, render_template, request
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import re
import numpy as np
import nltk
from nltk.stem.snowball import EnglishStemmer
import shlex
import pyinflect
from pyinflect import getAllInflections

#Initialize Flask instance
app = Flask(__name__)

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

tfv = TfidfVectorizer(lowercase=True, sublinear_tf=True, use_idf=True, norm="l2", stop_words=None, token_pattern=r'(?u)\b\w+\b')
sparse_matrix = tfv.fit_transform(documents).T.tocsr() # CSR: compressed sparse row format => order by terms

# 1-grams for exact match
tfv_1grams = TfidfVectorizer(lowercase=True, sublinear_tf=True, use_idf=True, norm="l2", stop_words=None, token_pattern=r'(?u)\b\w+\b', ngram_range=(1,1))
sparse_matrix_1grams = tfv_1grams.fit_transform(documents).T.tocsr() # CSR: compressed sparse row format => order by terms

# 2-grams for exact match
tfv_2grams = TfidfVectorizer(lowercase=True, sublinear_tf=True, use_idf=True, norm="l2", stop_words=None, token_pattern=r'(?u)\b\w+\b', ngram_range=(2,2))
sparse_matrix_2grams = tfv_2grams.fit_transform(documents).T.tocsr() # CSR: compressed sparse row format => order by terms

# 3-grams for exact match
tfv_3grams = TfidfVectorizer(lowercase=True, sublinear_tf=True, use_idf=True, norm="l2", stop_words=None, token_pattern=r'(?u)\b\w+\b', ngram_range=(3,3))
sparse_matrix_3grams = tfv_3grams.fit_transform(documents).T.tocsr() # CSR: compressed sparse row format => order by terms

t2i = cv.vocabulary_  # shorter notation: t2i = term-to-index

# stemming-related functions
#stemmer = EnglishStemmer()

#def stem_que(query):
#    return stemmer.stem(query) #returns stemmed query

#def stem_doc():
#    stem_single = []
#    stem_docs = []
#    for d in documents:
#        d = d.lower()
#        tok = word_tokenize(d)
#        for t in tok:
#            stem_single.append(" ".join(stemmer.stem(t)))
#            stem_docs.append("".join(stem_single))
#    return stem_docs #returns list of documents stemmed

def make_inf_list(query): # makes a list of all possible inflections for a query for non-exact matching                    
    all_inf = getAllInflections(query) # gets all inflections of the query and puts them in a dictionary (credits: https://github.com/bjascob/pyInflect)
    all_inf_list = []
    for i in all_inf.values(): # we only want the values in the dict
        inf = re.sub(r'\W+', '', str(i)) # make a string of the inflections
        if inf not in all_inf_list:
            all_inf_list.append(inf) # add to searchlist only if there are no duplicates
    neat_list = str(all_inf_list)[1:-1] # neat list without square brackets for display :)
    inf_query = " OR ".join(all_inf_list)
    print(f"List of words to look for: {neat_list}")
    return inf_query #return query as a modified query in format "query OR queries OR quering OR queried"

# boolean search-related functions

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
           matches.append({'name': documents_titles[doc_idx], 'text': documents[doc_idx][:300]}) #TODO don't restrict here
    return matches

def ranking_search(user_query):
    matches = []
    if re.fullmatch("\".+\"", user_query): # Finds exact queries
        user_query_stripped = user_query[1:-1]
        tfv_grams = tfv
        sparse_matrix_grams = sparse_matrix

        # choose the correct length to only match that string
        if len(user_query_stripped.split(" ")) == 1:
            tfv_grams = tfv_1grams
            sparse_matrix_grams = sparse_matrix_1grams
        elif len(user_query_stripped.split(" ")) == 2:
            tfv_grams = tfv_2grams
            sparse_matrix_grams = sparse_matrix_2grams
        elif len(user_query_stripped.split(" ")) == 3:
            tfv_grams = tfv_3grams
            sparse_matrix_grams = sparse_matrix_3grams
        else:
            return []

        query_vec = tfv_grams.transform([user_query_stripped]).tocsc()
        hits = np.dot(query_vec, sparse_matrix_grams)
        try:
            ranked_scores_and_doc_ids = sorted(zip(np.array(hits[hits.nonzero()])[0], hits.nonzero()[1]), reverse=True)
            for score, i in ranked_scores_and_doc_ids[:10]: #TODO don't restrict here
                matches.append({'name': documents_titles[i], 'text': documents[i][:300], 'score' : score}) #TODO don't restrict here
        except IndexError:
            #TODO better error handling
            return []

    else:
        try:
# commenting out the stemming for now
#            if bool(re.search(r"\".+\"", user_query)) is False:
#                user_query = stem_que(user_query)
#            else:
#                None
            query_vec = tfv.transform([user_query]).tocsc()
            hits = np.dot(query_vec, sparse_matrix)
            ranked_scores_and_doc_ids = sorted(zip(np.array(hits[hits.nonzero()])[0], hits.nonzero()[1]), reverse=True)
            for score, i in ranked_scores_and_doc_ids[:10]: #TODO don't restrict here
                matches.append({'name': documents_titles[i], 'text': documents[i][:300], 'score' : score}) #TODO don't restrict here
        except SyntaxError:
            #TODO better error handling
            return []
        except IndexError:
            #TODO better error handling
            return []

    return matches

@app.route('/')
def hello_world():
   return "Hello, World!"

#Function search() is associated with the address base URL + "/search"
@app.route('/search')
def search():

    #Get query from URL variable
    query = request.args.get('query')
    #TODO this needs to be passed to the template to keep the right button selected
    search_type = request.args.get('search_type')


    #Initialize list of matches
    matches = []

    #If query exists (i.e. is not None)
    if query:
        if search_type == "boolean_search":
            matches = boolean_test_query(f"{query}")
        elif search_type == "ranking_search":
            matches = ranking_search(f"{query}")

    #Render index.html with matches variable
    return render_template('index.html', matches=matches)
