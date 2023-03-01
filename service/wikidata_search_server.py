from flask import Flask, render_template, request
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import re
import numpy as np
import nltk
import simplemma
import pyinflect
import math
from pyinflect import getAllInflections
import shlex
import urllib.parse
import spacy
from spacy import displacy
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import random
import datetime
import time
import os



#Initialize Flask instance
app = Flask(__name__)

# read articles from file
absolute_path = os.path.dirname(__file__)
relative_path = "../data/"
full_path = os.path.join(absolute_path, relative_path)
with open(full_path + 'enwiki-20181001-corpus.1000-articles.txt', encoding='utf8') as f:
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


# Necessary dependency for spaCy:
ner_spacy = spacy.load("en_core_web_sm")

# Categories for highlighting named entities:
# category is active if the category is checked, name is the same as the entity category that spaCy uses, title should be human readable for the html form
spacy_categories = [
    {"active" : False, "name" : "PERSON", "title" : "People"}, 
    {"active" : False, "name" : "DATE", "title" : "Dates"},
    {"active" : False, "name" : "LANGUAGE", "title" : "Languages"},
    {"active" : False, "name" : "GPE", "title" : "Countries, cities and states"}
]


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
    
    return inf_token #return token with added inflections in format "token OR tokens OR tokened OR tokening"  


def check_for_inflections(query): # reads the query and returns a rewritten query that includes inflections when a searchword is not enclosed in quotation marks
    rewritten = ""
    counter = 0 # counter for last if-statement
    token_list = query.split() # split query into individual tokens
    for i in token_list:
        if i.isupper() is True: 
            rewritten += " " + i # add uppercase tokens (operators) to string as they are
        elif "\"" in i:
            rewritten += " " + i # add tokens enclosed by quotation marks to string as-is
            counter += 1
        elif re.match(r"\W" ,i): # add any non-word character (such as brackets) to string as-is
            rewritten += " " + i
        else:
            single_token_inflected = single_token_inflection(i)
            if (single_token_inflected.strip()): # add token only if any inflections are found
                rewritten += " ( " + single_token_inflected + " )" # add lowercase unquoted tokens with all their possible inflections to string enclosed by brackets
            else:
                rewritten += " ( " + i + " )" # otherwise add token as-is 
            counter += 1
    if counter == 1 : # if the initial query consisted of only one token...
        rewritten = re.sub(r" [\(\)]", "", rewritten) # remove unneeded brackets from initial query
    rewritten = rewritten.strip()
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
    rewritten_query = boolean_rewrite_query(query)
    # check for ) ( since it might create an attempt to call the function, and this is not a syntax error even though it is the wrong syntax
    if re.match(".*\)\s*\(.*", rewritten_query):
        return [], "Unknown word, no matches found for the search query. Make sure your query is typed in as instructed."
    matches = []
    try:
        if np.all(eval(rewritten_query) == 0):
            return [], ""
        else:
            hits_matrix = eval(rewritten_query)
            hits_list = list(hits_matrix.nonzero()[1])
            for doc_idx in hits_list:
                # This line works for version with spaCy highlighting (spaCy recognizes the linebreaks automatically):
                matches.append({'name': documents_titles[doc_idx], 'text': documents[doc_idx]})
                # This is the working version without spaCy, DO NOT ERASE:
                # matches.append({'name': documents_titles[doc_idx], 'text': documents[doc_idx].replace("\n", "<br />")})

    except SyntaxError:
        return [], "Unknown word, no matches found for the search query. Make sure your query is typed in as instructed."
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
                # This line works for version with spaCy highlighting (spaCy recognizes the linebreaks automatically):
                matches.append({'name': documents_titles[i], 'text': documents[i], 'score' : score})
                # This is the working version without spaCy, DO NOT ERASE:
                # matches.append({'name': documents_titles[i], 'text': documents[i].replace("\n", "<br />"), 'score' : score})

        except IndexError:
            return [], "Unknown word, no matches found for the search query. Make sure your query is typed in as instructed."

    else:
        try:
            query_vec = tfv.transform([user_query]).tocsc()
            hits = np.dot(query_vec, sparse_matrix)
            ranked_scores_and_doc_ids = sorted(zip(np.array(hits[hits.nonzero()])[0], hits.nonzero()[1]), reverse=True)
            for score, i in ranked_scores_and_doc_ids:
                # This line works for version with spaCy highlighting (spaCy recognizes the linebreaks automatically):
                matches.append({'name': documents_titles[i], 'text': documents[i], 'score' : score})
                # This is the working version without spaCy, DO NOT ERASE:
                # matches.append({'name': documents_titles[i], 'text': documents[i].replace("\n", "<br />"), 'score' : score})

        except SyntaxError:
            return [], "Unknown word, no matches found for the search query. Make sure your query is typed in as instructed."
        except IndexError:
            return [], "Unknown word, no matches found for the search query. Make sure your query is typed in as instructed."

    return matches, ""

def create_url(search_type, query, page):
    return "/?search_type={:s}&query={:s}&page={:d}".format(search_type, urllib.parse.quote(query), page)
    

def generate_query_plot(query,matches):
    if len(matches) == 0:
        return False;
    dist_dict={}

    for match in matches:
        # TODO this is only for dummy purposes, real data will contain dates
        document_week_date = date_aggregated(random_date())
        if document_week_date in dist_dict.keys():
            dist_dict[document_week_date] += 1
        else:
            dist_dict[document_week_date] = 1

    plt.figure().set_figwidth(15)
    plt.title(f"Document distribution \n query: {query}")
    ax = plt.subplot()

    # bar chart with from counted values
    ax.bar(dist_dict.keys(), dist_dict.values(), width=1)
    # set y axis to full integer ticks
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))


    # set xaxis as dates
    ax.xaxis_date()
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    # save chart to file
    relative_path = f'static/query_{query}_plot.png'
    plt.savefig(os.path.join(absolute_path, relative_path))
    return relative_path

def date_aggregated(date):
    """ Displaying every document on its own date will not fit, currently aggregating dates to the Monday of their week """
    return date - datetime.timedelta(days=date.weekday())


# TODO remove, for dummy use only
def random_date():

    now_date = datetime.datetime.now()
    random_days = datetime.timedelta(days=random.randrange(1825))
    return now_date - random_days

'''
@app.route('/hello')
def hello_tiramisu():
   return "Hello! Welcome to TIRAMISU search webpage. Access the search engine by removing \"/hello\" at the end of this webpage's URL."
'''

#Function search() is associated with the address base URL
@app.route('/')
def search():

    #Get values from URL variables
    query = request.args.get('query', "")
    search_type = request.args.get('search_type', "boolean_search")
    page = max(int(request.args.get('page', "1")), 1)

    #Initialize list of matches
    matches = []
    error = ""

    #If query exists (i.e. is not None)
    if query:
        if search_type == "boolean_search":
            (matches, error) = boolean_test_query(f"{query}")
        elif search_type == "ranking_search":
            (matches, error) = ranking_search(f"{query}")

    plot_file = generate_query_plot(query, matches)

    #Variables for paging
    documents_per_page = 10
    shown_pagination_range_one_direction = 2
    page_count = math.ceil(len(matches)/documents_per_page)
    page = min(page, page_count)
    matches_shown = matches[(page - 1)*documents_per_page:page*documents_per_page]


    # Named entity highlighting with spaCy
    # making a list of the entities (ents) the user has chosen to highlight:
    chosen_ents = []
    for category in spacy_categories:
        if request.args.get(category["name"]) is not None:
            chosen_ents.append(request.args.get(category["name"]))
        category['active'] = request.args.get(category["name"], False)

    if chosen_ents != []:
        print("Chosen entities:", chosen_ents)
        
    # modifying text items of the matches_shown variable with the chosen ents and their corresponding colors:
    for match in matches_shown:
        text = match["text"]
        spacy_text = ner_spacy(text)
        colors = {"PERSON": "#BECDF4", "DATE": "#ADD6D6", "LANGUAGE": "#F0DDB8", "GPE": "#E5E9E9"}
        options = {"ents": chosen_ents, "colors": colors}
        spacy_html = displacy.render(spacy_text, style="ent", options=options)
        match["text"] = spacy_html
    

    # create pagination
    pages = []
    if page_count > 1:
        if page > 1:
            pages.append({'url': create_url(search_type, query, page - 1), 'name': '<'})
        if page > shown_pagination_range_one_direction + 1:
            pages.append({'url': create_url(search_type, query, 1), 'name': 1})
        if page > shown_pagination_range_one_direction + 2:
            pages.append({'url': False, 'name': '...'})
        for index in range(max(1, page - shown_pagination_range_one_direction), min(page_count+1, page + shown_pagination_range_one_direction + 1)):
            pages.append({'url': create_url(search_type, query, index) if page != index else False, 'name': index})
        if page < page_count - shown_pagination_range_one_direction - 1:
            pages.append({'url': False, 'name': '...'})
        if page < page_count - shown_pagination_range_one_direction:
            pages.append({'url': create_url(search_type, query, page_count), 'name': page_count})
        if page < page_count:
            pages.append({'url': create_url(search_type, query, page + 1), 'name': '>'})

    #Render index.html with matches variable
    return render_template('index.html', 
        matches=matches_shown, 
        error=error, 
        query=query, 
        search_type=search_type, 
        docs_total=str(len(matches)), 
        pages=pages, 
        spacy_categories=spacy_categories,
        plot=plot_file
    )
