from flask import Flask, render_template, request
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import re
import numpy as np
import nltk
import simplemma
import pyinflect
from pyinflect import getAllInflections
import shlex

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


# functions related to non-exact-word matching
def single_token_inflection(query): # makes a list of all possible inflections of a token for non-exact matching                                                
    query = simplemma.lemmatize(query, lang="en") # lemmatizes query in case the token is in inflected form in the query
    all_inf = getAllInflections(query) # gets all inflections of the token and sets them as value in a dictionary (\credits: https://github.com/bjascob/pyInflect)
    all_inf_list = []
    for i in all_inf.values(): # we only want the values in the generated dict                                 
        inf = re.sub(r'\W+', '', str(i)) # make a string of the inflections                                
        if inf not in all_inf_list:
            all_inf_list.append(inf) # add to searchlist only if there are no duplicates                                  
    inf_token = " OR ".join(all_inf_list)
    # print(inf_token)
    return inf_token #return token with added inflections in format "token OR tokens OR tokened OR tokening"  


def check_for_inflections(query): # reads the query and returns a rewritten query that includes inflections when a searchword is not enclosed in quotation marks
    rewritten = ""
    counter = 0 # counter for last if-statement
    token_list = query.split() # split query into individual tokens
    for i in token_list:
        if i.isupper() is True: 
            #print(i) 
            rewritten += " " + i # add uppercase tokens (operators) to string as they are
        elif "\"" in i:
            #print(i)
            rewritten += " " + i # add tokens enclosed by quotation marks to string as-is
            counter += 1
        elif re.match(r"\W" ,i): # add any non-word character (such as brackets) to string as-is 
            rewritten += " " + i
        else:
            #print(i)
            rewritten += " ( " + single_token_inflection(i) + " )" # add lowercase unquoted tokens with all their possible inflections to string enclosed by brackets
            counter += 1
    if counter == 1 : # if the initial query consisted of only one token...
        rewritten = re.sub(r" [\(\)]", "", rewritten) # remove unneeded brackets from initial query
    return rewritten # return rewritten query

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
    return " ".join(boolean_rewrite_token(t) for t in shlex.split(query))

def boolean_test_query(query):
    print("Query: '" + query + "'")
    query = check_for_inflections(query)
    print("Query with added inflections: '" + query + " '")
    matches = []
    try:
        if np.all(eval(boolean_rewrite_query(query)) == 0):
            return [], ""
        else:
    #        print("Matching:", eval(boolean_rewrite_query(query))) # Eval runs the string as a Python command
            hits_matrix = eval(boolean_rewrite_query(query))
            hits_list = list(hits_matrix.nonzero()[1])
            for doc_idx in hits_list:
               matches.append({'name': documents_titles[doc_idx], 'text': documents[doc_idx].replace("\n", "<br />")
})
    except SyntaxError:
        return [], "The input was erroneous, cannot show results.\nMake sure the operators are typed in ALLCAPS."
    return matches, ""

def ranking_search(user_query):
    user_query = check_for_inflections(user_query)
    print("Query with added inflections: '" + user_query + " '")
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
            for score, i in ranked_scores_and_doc_ids:
                matches.append({'name': documents_titles[i], 'text': documents[i].replace("\n", "<br />"), 'score' : score})
        except IndexError:
            return [], "Unknown word, no matches found for the search query."

    else:
        try:
            query_vec = tfv.transform([user_query]).tocsc()
            hits = np.dot(query_vec, sparse_matrix)
            ranked_scores_and_doc_ids = sorted(zip(np.array(hits[hits.nonzero()])[0], hits.nonzero()[1]), reverse=True)
            for score, i in ranked_scores_and_doc_ids:
                matches.append({'name': documents_titles[i], 'text': documents[i].replace("\n", "<br />"), 'score' : score})
        except SyntaxError:
            return [], "The input was erroneous, cannot show results.\nMake sure your query is typed in as instructed."
        except IndexError:
            return [], "Unknown word, no matches found for the search query."

    return matches, ""

@app.route('/')
def hello_tiramisu():
   return "Hello! Welcome to TIRAMISU search webpage. Access the search engine by adding \"/search\" at the end of this webpage's URL."

#Function search() is associated with the address base URL + "/search"
@app.route('/search')
def search():

    #Get query from URL variable
    query = request.args.get('query', "")
    search_type = request.args.get('search_type', "boolean_search")

    #Initialize list of matches
    matches = []
    error = ""
    
    #If query exists (i.e. is not None)
    if query:
        if search_type == "boolean_search":
            (matches, error) = boolean_test_query(f"{query}")
        elif search_type == "ranking_search":
            (matches, error) = ranking_search(f"{query}")

    #Render index.html with matches variable
    #todo paging to show all results?
    return render_template('index.html', matches=matches[:10], error=error, query=query, search_type=search_type, docs_total=str(len(matches)))
