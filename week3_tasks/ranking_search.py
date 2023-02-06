from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import numpy as np
import nltk
from nltk.stem.snowball import EnglishStemmer

# read articles from file
with open('../data/enwiki-20181001-corpus.1000-articles.txt', encoding='utf8') as f:
    content = f.read()

# split by closing article tag, and then remove opening tag
# save document titles in separate array
documents = content.strip().split('</article>')
p = re.compile('^\s*<article\s+name="(.*?)"\s*>\s*')
documents_titles = [p.match(document).group(1) for document in documents if document and p.match(document)]
documents = [re.sub(p, "", document) for document in documents if document and p.match(document)]

# define stemmer
stemmer = EnglishStemmer()

def stem_que(query):
    query = stemmer.stem(query)
    return query
    
def boolean_query_matrix(t):
    """
    Checks if the term is present in any of the documents.
    If present, returns the hits matrix, and if not, an empty row to be used in calculations
    """
    return sparse_td_matrix[t2i[t]].todense() if t in t2i.keys() else np.array([[0] * len(documents)])

def boolean_rewrite_token(t):
    return d.get(t, 'boolean_query_matrix("{:s}")'.format(t)) 

def boolean_rewrite_query(query): # rewrite every token in the query
    if bool(re.search(r'\".+\"', query)) is False:
        query = stem_que(query)
    else:
        query = re.sub('\"','', query)
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
        # Here we print only the first 10 matching documents and only the first 1000 characters from those documents:
        doc_number = 1
        for doc_idx in hits_list[:10]:
            print(f"\nMatching doc #{doc_number}: \n")
            print_document(documents[doc_idx])
            doc_number += 1


def print_document(document, char_limit = 1000):
    if (len(document) > char_limit):
        print(document[:char_limit] + "...")
    else:
        print(document)

# Boolean search program that asks the user for a search query, program quits when an empty string is entered
def boolean_search():
    cv = CountVectorizer(lowercase=True, binary=True, stop_words=None, token_pattern=r'(?u)\b\w+\b')
    sparse_matrix = cv.fit_transform(documents)
    global sparse_td_matrix
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

    # Let's print some instructions on the Boolean search query for the user:
    print("\n*** The searh query should be of the form of the following examples: ***\n")

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

# Ranking search program that asks the user for a search query, program quits when an empty string is entered
def ranking_search():
    tfv = TfidfVectorizer(lowercase=True, sublinear_tf=True, use_idf=True, norm="l2", stop_words=None, token_pattern=r'(?u)\b\w+\b')
    sparse_matrix = tfv.fit_transform(documents).T.tocsr() # CSR: compressed sparse row format => order by terms

    # First let's print some instructions on the Ranking search query for the user:
    print("\n*** The search query should be of the form of the following examples: ***\n")

    print("    When searched for one word or multiple different words, type words separated by space:")
    print("    word anotherword lastword")
    print("    When searching for intact multi-word phrases (only bigrams or trigrams), use quotation marks:")
    print("    \"New York\"")

    print("\n*** Search words can be written in lowercase or uppercase letters, query needs to contain at least one letter. ***")
    
    while True:
        user_query = str(input("\nEnter your query (empty string quits program): \n"))
        if user_query == "":
            break
        elif re.fullmatch("\W+", user_query):
            print("\n*** The input was erroneous, cannot show results.\nMake sure your query is typed in as instructed. ***\n")
        elif re.fullmatch("\".+\s.+\"", user_query): # Finds multi-word search queries
            print("Quotation marks found, let's now handle this as one phrase and not separate words") #This is for testing //Tiia
        else:
            try:
                if bool(re.search(r"\".+\"", user_query)) is False:
                    user_query = stem_que(user_query)
                else:
                    None
                query_vec = tfv.transform([user_query]).tocsc()
                hits = np.dot(query_vec, sparse_matrix)
                ranked_scores_and_doc_ids = sorted(zip(np.array(hits[hits.nonzero()])[0], hits.nonzero()[1]), reverse=True)
                # Here we print only the first 10 matching documents and only the first 1000 characters from those documents:
                print("\nResults:")
                print(f"Query: {user_query}")
                print(f"{len(ranked_scores_and_doc_ids)} matching documents in total.")
                doc_number = 1
                for score, i in ranked_scores_and_doc_ids[:10]:
                    print("\nThe score of '{:s}' is {:.4f} in document #{:}: \n".format(user_query, score, doc_number))
                    print_document(documents[i])
                    doc_number += 1
            except SyntaxError:
                print("\n*** The input was erroneous, cannot show results.\nMake sure your query is typed in as instructed. ***\n")
            except IndexError:
                print(f"\nUnknown word, no matches found for the search query: {user_query}\n")
    

# The main search engine works here:

def main():
    print("Search engine starts...")

    # Here we'll let the user decide which search engine is going to be used (Boolean or ranking):
    while True:
        engine_choice = str(input("\nChoose your search engine:\n1: Boolean search\n2: Ranking search method\n\nEnter your choice by typing 1 or 2 (empty string quits program): "))
        if engine_choice == "":
            break
        elif engine_choice == "1" or engine_choice == "2":        
            if engine_choice == "1":
                boolean_search()
                break
            elif engine_choice == "2":
                ranking_search()
                break
        else:
            print("\n*** The input was erroneous, search engine is chosen by only typing 1 or 2. ***\n")

    print("\nSearch engine closed")


    
#Let's call the main function here:
main()
