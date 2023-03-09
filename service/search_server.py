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
import json
from dateutil import parser
import unicodedata

plt.switch_backend('Agg') # Added to avoid site crashing on mac

#Initialize Flask instance
app = Flask(__name__)

# template formatter for unifying shown dates
@app.template_filter()
def format_date(value):
    mydate = parser.parse(value)
    return mydate.strftime('%Y-%m-%d')

# Reading articles from fanfic files of 2018-2022 in data folder
# Parsing the json files and converting the contents of each file into python dictionary form
absolute_path = os.path.dirname(__file__)
relative_path = "../data/"
full_path = os.path.join(absolute_path, relative_path)
with open(full_path + 'fanfics2018.json', encoding='utf8') as fic18:
    content18 = fic18.read()
    content18 = json.loads(content18)
with open(full_path + 'fanfics2019.json', encoding='utf8') as fic19:
    content19 = fic19.read()
    content19 = json.loads(content19)
with open(full_path + 'fanfics2020.json', encoding='utf8') as fic20:
    content20 = fic20.read()
    content20 = json.loads(content20)
with open(full_path + 'fanfics2021.json', encoding='utf8') as fic21:
    content21 = fic21.read()
    content21 = json.loads(content21)
with open(full_path + 'fanfics2022.json', encoding='utf8') as fic22:
    content22 = fic22.read()
    content22 = json.loads(content22)

# Combining all contents to one file that can then be processed at once
documents = content18 + content19 + content20 + content21 + content22

"""
Metadata can be extracted from the fanfic articles in this manner:
fic_date = documents[index]['date_published'][:10] --> the date is in the form: 2018-12-25
fic_title = documents[index]['title']
fic_id = documents[index]['id']
fic_categories = documents[index]['categories'] --> a list
fic_characters = documents[index]['characters'] --> a list
fic_fandoms = documents[index]['characters'] --> a list
fic_tags = documents[index]['tags'] --> a list
fic_warnings = documents[index]['warnings'] --> a list
fic_text = documents[index]['content'] --> this is the article text, all headlines within text are placed inside <h3></h3> tags and the paragraphs inside <p></p> tags for html
"""

# Creating variables from the data to be used in the program
fic_all_dates = []
fic_all_titles = []
fic_all_texts = []
fic_all_warnings = []

index = 0
for item in documents:    
    fic_date = documents[index]['date_published'][:10]
    fic_all_dates.append(fic_date)
    fic_title = documents[index]['title']
    fic_all_titles.append(fic_title)
    fic_text = documents[index]['content']
    fic_all_texts.append(fic_text)
    fic_warnings = documents[index]['warnings']
    fic_all_warnings.append(fic_warnings)
    index += 1

works = documents
documents_titles = fic_all_titles
documents = fic_all_texts
warnings = fic_all_warnings

cv = CountVectorizer(lowercase=True, binary=True, stop_words=None, token_pattern=r'(?u)\b\w+\b', ngram_range=(1,3))
sparse_matrix = cv.fit_transform(documents)
sparse_td_matrix = sparse_matrix.T.tocsr()

# Operator replacements:
d = {"AND": "&",
     "OR": "|",
     "NOT": "1 -",
     "(": "(", ")": ")"}
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
    all_inf_list = [ query ] # put original query in list of all inflections
    if getAllInflections(query) == {}: # if getAllInflections returns nothing (if the query is an inflected term)
        query = simplemma.lemmatize(query, lang="en") # lemmatizes query before inflection
    else:
        None
    all_inf = getAllInflections(query) # gets all inflections of the token and sets them as value in a dictionary
    for i in all_inf.values(): # we only want the values in the generated dict
        stringed = re.sub(r'[^\w\s]', '', str(i)) # make a string of the dictionary values (remove anything besides word or space characters)
        inf = re.sub(r'[\s]', ' OR ', stringed) # whether there is a space character, replace it with ' OR ' as it implies the dictionary value in question contained more than one token
        if inf not in all_inf_list:
            all_inf_list.append(inf) # add to searchlist only if there are no duplicates
    inf_token = " OR ".join(all_inf_list)
    
    return inf_token #return token with added inflections in format "token OR tokens OR tokened OR tokening"  

def check_for_inflections(query): # reads the query and returns a rewritten query that includes inflections when a searchword is not enclosed in quotation marks
    rewritten = ""
    counter = 0 # counter for last if-statement
    token_list = query.split() # split query into individual tokens
    is_quote_open = False
    for i in token_list:
        if is_quote_open or i.startswith("\""):
            is_quote_open = True
            rewritten += " " + i # add tokens enclosed by quotation marks to string as-is
            if i.endswith("\""):
                is_quote_open = False # quote ends
                counter += 1
        elif i.isupper() is True: 
            rewritten += " " + i # add uppercase tokens (operators) to string as they are
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


# function for making list of inflected forms of the search query
def inflections(query):
    inflections_list = re.split(" *OR *| *AND *| *NOT *|\( | \)", query)
    query_list = []
    for item in inflections_list:
        # if item is empty, don't take into account:
        if item == "" or item == " ":
            continue
        # if query is an exact match, loose quotation marks:
        elif re.fullmatch("\".+\"", item):
            exact_query = re.sub("\"", "", item)
            capital_firstword = exact_query.replace(f"{exact_query}", f"{exact_query.capitalize()}")
            allwords = exact_query.split(" ")
            capital_allwords = ""
            for word in allwords:
                word = word.capitalize()
                if capital_allwords == "":
                    capital_allwords = word
                else:
                    capital_allwords = capital_allwords + " " + word
            query_list.append(exact_query)
            query_list.append(capital_firstword)
            query_list.append(capital_allwords)
        else:
            capital = item.replace(f"{item}", f"{item.capitalize()}")
            query_list.append(item)
            query_list.append(capital)

    return query_list


# error message
error_message = "Unknown query, no matches found for the search query. Make sure your query is typed in as instructed."

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
    query = check_for_inflections(query)
    print("Query with added inflections: '" + query + " '")
    inflections_list = inflections(query)
    print(f"Query inflections list: {inflections_list}")
    try:
        rewritten_query = boolean_rewrite_query(query)
    except ValueError:
        print(f"\n{error_message}\n")
        return [], error_message, []

    # check for ) ( since it might create an attempt to call the function, and this is not a syntax error even though it is the wrong syntax
    if re.match(".*\)\s*\(.*", rewritten_query):
        print(f"\n{error_message}\n")
        return [], error_message, []
    matches = []
    try:
        if np.all(eval(rewritten_query) == 0):
            return [], "", []
        else:
            hits_matrix = eval(rewritten_query)
            hits_list = list(hits_matrix.nonzero()[1])
            for doc_idx in hits_list:
                matches.append({'name': documents_titles[doc_idx], 'text': documents[doc_idx], 'work': works[doc_idx]})

    except SyntaxError:
        print(f"\n{error_message}\n")
        return [], error_message, []
    except IndexError:
        print(f"\n{error_message}\n")
        return [], error_message, []
    except ValueError:
        print(f"\n{error_message}\n")
        return [], error_message, []
    return matches, "", inflections_list


# ranking search related function
def ranking_search(user_query):
    user_query = check_for_inflections(user_query)
    inflections_list = inflections(user_query)
    print(f"Query inflections list: {inflections_list}")
    # remove ORs and parentheses since ranking search doesn't utilise them
    user_query = user_query.replace(" ( ", " ").replace(" ) ", " ").replace(" OR ", " ")
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
            return matches, "", inflections_list

        query_vec = tfv_grams.transform([user_query_stripped]).tocsc()
        hits = np.dot(query_vec, sparse_matrix_grams)
        try:
            ranked_scores_and_doc_ids = sorted(zip(np.array(hits[hits.nonzero()])[0], hits.nonzero()[1]), reverse=True)
            for score, i in ranked_scores_and_doc_ids:
                matches.append({'name': documents_titles[i], 'text': documents[i], 'score' : score, 'work': works[i]})

        except SyntaxError:
            print(f"\n{error_message}\n")
            return [], error_message, []
        except IndexError:
            print(f"\n{error_message}\n")
            return matches, error_message, inflections_list

    else:
        try:
            query_vec = tfv.transform([user_query]).tocsc()
            hits = np.dot(query_vec, sparse_matrix)
            ranked_scores_and_doc_ids = sorted(zip(np.array(hits[hits.nonzero()])[0], hits.nonzero()[1]), reverse=True)
            for score, i in ranked_scores_and_doc_ids:
                matches.append({'name': documents_titles[i], 'text': documents[i], 'score' : score, 'work': works[i]})

        except SyntaxError:
            print(f"\n{error_message}\n")
            return matches, error_message, inflections_list
        except IndexError:
            print(f"\n{error_message}\n")
            return matches, error_message, inflections_list

    return matches, "", inflections_list



def create_url(search_type, query, page):
    return "/?search_type={:s}&query={:s}&page={:d}".format(search_type, urllib.parse.quote(query), page)
    

# plot/graph related functions
def generate_query_plot(query,matches):
    if len(matches) == 0:
        return False;
    dist_dict={}

    for match in matches:
        if not match['work']['date_published']:
            continue
        yourdate = parser.parse(match['work']['date_published'])
        document_week_date = date_aggregated(yourdate)
        if document_week_date in dist_dict.keys():
            dist_dict[document_week_date] += 1
        else:
            dist_dict[document_week_date] = 1

    # calculate required width
    # we count the days between start and end, and translate it to months
    time_difference = max(dist_dict.keys()) - min(dist_dict.keys())
    time_difference_in_months = time_difference.days / 356 * 12

    # create plot
    plt.figure(figsize=(max(time_difference_in_months * 0.2, 6.4),4.8))
    plt.gcf().subplots_adjust(bottom=0.20)
    plt.title(f"Monthly distribution of the documents", ha='left', x=-0)   
    ax = plt.subplot()

    # bar chart with from counted values
    ax.bar(dist_dict.keys(), dist_dict.values(), width=25)
    # set y axis to full integer ticks
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # set xaxis as dates
    ax.xaxis_date()

    if time_difference_in_months > 12: # we have multiple years of data

        # Set minor ticks to months
        ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=1))

        # set major ticks to year
        ax.xaxis.set_major_locator(mdates.YearLocator())

        # set formatter
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    else: # less than a year, format with monthly major ticks

        # Set major ticks to months
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))

        # set formatter
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    # set rotation for date tick labels 
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    # save chart to file
    safe_query = safe_filename(query)
    relative_path = f'static/query_{safe_query}_plot.png'
    plt.savefig(os.path.join(absolute_path, relative_path), bbox_inches='tight')
    return relative_path

def generate_warning_plot(query, matches):    # for generating scatter plot which takes date_published, warnings and their frequency as values
    if len(matches) == 0:
        return False;
    
    datadict = {}   # dict to collect all data from matches neatly into keys of dates. The values consist of a list of dicts with warnings as keys for each dict and their respective occurrences on the key date as values
    for match in matches:    
        date = match['date_published'][0]
        warn = match['warnings']
        if datadict == {} :  
            datadict[date] = [{'Major Character Death': 0},{'No Archive Warnings Apply': 0}, {'Rape/Non-con': 0},
                          {'Underage': 0},{'Graphic Depictions Of Violence': 0},{'Creator Chose Not To Use Archive Warnings': 0}]
            for w in warn:
                for item in datadict[date]:
                    if w in item.keys():
                        item[w] += 1
        else :
            if date in datadict.keys():
                for w in warn:
                    for item in datadict[date]:
                        if w in item.keys():
                            item[w] += 1
            else:
                datadict[date] = [{'Major Character Death': 0},{'No Archive Warnings Apply': 0}, {'Rape/Non-con': 0},
                          {'Underage': 0},{'Graphic Depictions Of Violence': 0},{'Creator Chose Not To Use Archive Warnings': 0}]
                for w in warn:
                    for item in datadict[date]:
                        if w in item.keys():
                            item[w] += 1

    # Arranging data into lists for x and y axis and s value of scatter plot
    x = []    #values for x axis
    y = []    #values for y axis
    z = []    #values to determine s

    for date in datadict:
        for warning in datadict[date]:
            for n in warning.values():
                if n != 0 :
                    y.append((datadict[date].index(warning) + 1))
                    z.append(n)
                    x.append(date)
    # I have yet to figure out how to create the scatter plot
    plt.figure(figsize=(max(60 * 0.2, 6.4),4.8)) #TODO change to be similar to other plot
    plt.gcf().subplots_adjust(bottom=0.20)
    plt.title(f"Distribution and amount of content warnings in months", ha='left', x=-0)   
    ax = plt.subplot()
    #ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.scatter(x, y, s=z)

    # save chart to file                                                                                                                                                                                    
    safe_query = safe_filename(query)
    relative_path = f'static/query_{safe_query}_warning.png'
    plt.savefig(os.path.join(absolute_path, relative_path), bbox_inches='tight')
                
def date_aggregated(date):
    """ Displaying every document on its own date will not fit, currently aggregating dates to the 1st month """
    return date - datetime.timedelta(days=date.day)

def safe_filename(query):
    """
    Make query safe for filename
    From https://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filena
    """
    value = unicodedata.normalize('NFKD', query).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')

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

    #Initialize list of matches and list of query inflections
    matches = []
    error = ""
    inflections_list = []

    #If query exists (i.e. is not None)
    if query:
        print(f"Query: {query}")
        if search_type == "boolean_search":
            print("Search type:", search_type)
            (matches, error, inflections_list) = boolean_test_query(f"{query}")
        elif search_type == "ranking_search":
            print("Search type:", search_type)
            (matches, error, inflections_list) = ranking_search(f"{query}")

    plot_file = generate_query_plot(query, matches)

    #Variables for paging
    documents_per_page = 10
    shown_pagination_range_one_direction = 2
    page_count = math.ceil(len(matches)/documents_per_page)
    page = min(page, page_count)
    matches_shown = matches[(page - 1)*documents_per_page:page*documents_per_page]


    # Named entity highlighting with spaCy AND emphasizing query words and their inflected forms within the matching fanwork texts

    # First, we'll make a list of the entities (ents) that the user has chosen to highlight (with spaCy):
    chosen_ents = []
    for category in spacy_categories:
        if request.args.get(category["name"]) is not None:
            chosen_ents.append(request.args.get(category["name"]))
        category['active'] = request.args.get(category["name"], False)

    # Second, if user has chosen to highlight entities:
    # we'll modify text items of the matches_shown variable with the chosen ents and their corresponding colors
    if chosen_ents != []:
        print(f"Chosen entities: {chosen_ents}\n")
        for match in matches_shown:
            text = match["text"]
            # (because of reasons concerning temporary memory, spaCy highlighting is only processed for the first 100 000 characters of each document)
            if len(text) > 100000:
                beginning_of_text = text[0:100000]
                rest_of_text = text[100000:]
                spacy_text = ner_spacy(beginning_of_text)
                colors = {"PERSON": "#BECDF4", "DATE": "#ADD6D6", "LANGUAGE": "#F0DDB8", "GPE": "#E5E9E9"}
                options = {"ents": chosen_ents, "colors": colors}
                spacy_html = displacy.render(spacy_text, style="ent", options=options)
                # replace all words in inflections_list with different styling (class in the index.html) in spacy_html
                for item in inflections_list:
                    text = spacy_html
                    bolded_text = re.sub(rf"(</br>|[ ‘`´'“\"])({item})(</br>|[ .,:;!?’´`'”\"]+)", r'\1<b class="query-words">\2</b>\3', text)
                    spacy_html = bolded_text
                # replace all words in inflections_list with different styling (class in the index.html) in rest_of_text
                rest_of_text = rest_of_text.replace("\n", "<br />")
                for item in inflections_list:
                    rest_of_text = re.sub(rf"(<br />|[ ‘`´'“\"])({item})(<br />|[ .,:;!?’´`'”\"]+)", r'\1<b class="query-words">\2</b>\3', rest_of_text)
                # combine the spacied text and rest of the text
                whole_text = spacy_html + rest_of_text
                match["text"] = whole_text
            else:
                spacy_text = ner_spacy(text)
                colors = {"PERSON": "#BECDF4", "DATE": "#ADD6D6", "LANGUAGE": "#F0DDB8", "GPE": "#E5E9E9"}
                options = {"ents": chosen_ents, "colors": colors}
                spacy_html = displacy.render(spacy_text, style="ent", options=options)
                match["text"] = spacy_html
                # replace all words in inflections_list with different styling (class in the index.html) in spacy_html
                for item in inflections_list:
                    text = match["text"]
                    bolded_text = re.sub(rf"(</br>|[ ‘`´'“\"])({item})(</br>|[ .,:;!?’´`'”\"]+)", r'\1<b class="query-words">\2</b>\3', text)
                    match["text"] = bolded_text
                
    # If user has chosen not to highlight any entities, we'll only emphasize the query words:
    else:
        for match in matches_shown:
            match["text"] = match["text"].replace("\n", "<br />")
            # replace all words in inflections_list with different styling (class in the index.html) in match["text"]
            for item in inflections_list:
                text = match["text"]
                bolded_text = re.sub(rf"(<br />|[ ‘`´'“\"])({item})(<br />|[ .,:;!?’´`'”\"]+)", r'\1<b class="query-words">\2</b>\3', text)
                match["text"] = bolded_text


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
