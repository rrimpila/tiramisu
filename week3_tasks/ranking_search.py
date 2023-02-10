from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import numpy as np
import nltk
from nltk.stem.snowball import EnglishStemmer
from nltk.tokenize import word_tokenize
import shlex 

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
    if np.all(eval(boolean_rewrite_query(query)) == 0):
        print("No matches: there are no documents matching the query '" + query + "'")
        print("______________________________________________________________________________________________________________________")
    else:
        print("Matching:", eval(boolean_rewrite_query(query))) # Eval runs the string as a Python command
        hits_matrix = eval(boolean_rewrite_query(query))
        hits_list = list(hits_matrix.nonzero()[1])
        print(str(len(hits_list)) + " matching documents in total.")
        print("______________________________________________________________________________________________________________________")
        # Here we print only the first 10 matching documents:
        doc_number = 1
        for doc_idx in hits_list[:10]:
            print(f"\n\nMatching document #{doc_number}: \n")
            print_document(documents[doc_idx])
            doc_number += 1

# Print document function, which prints the name of the doc and the first 300 characters from the beginning of it:
def print_document(document, char_limit = 300):
    if (len(document) > char_limit):
        print("Name: LET'S ADD DOC NAME HERE\n")
        print(f"Content: {document[:char_limit]}...")
        print("\n----------------------------------------------------------------------------------------------------------------------")
    else:
        print(document)

# Boolean search program that asks the user for a search query, program quits when an empty string is entered
def boolean_search():
    cv = CountVectorizer(lowercase=True, binary=True, stop_words=None, token_pattern=r'(?u)\b\w+\b', ngram_range=(1,3))
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
    print("\n**********************************************************************************************************************")
    print("\n   BOOLEAN SEARCH:")
    print("\n   Please form the searh query in the following manner:")
    print("       you AND i")
    print("       example AND NOT nothing")
    print("       NOT example OR great")
    print("       ( NOT example OR great ) AND nothing")
    print("\n   Use quotation marks when searching for intact multi-word phrases (the program only supports bigrams and trigrams):")
    print("       \"new york\"")
    print("\n   Multi-word phrases can also be combined with the Boolean operators:")
    print("       \"new york\" OR london")
    print("\n   Operators AND, OR, NOT need to be written in ALLCAPS, search words in lowercase.\n")
    print("**********************************************************************************************************************")
    
    while True:
        user_query = str(input("\n\nEnter your query (empty string quits Boolean search): "))
        if user_query == "":
            break
        else:
            try:
                print("\n\n______________________________________________________________________________________________________________________")
                print("\nRESULTS:")
                boolean_test_query(f"{user_query}")
            except SyntaxError:
                print("\n*** The input was erroneous, cannot show results.\nMake sure the operators are typed in ALLCAPS. ***\n")

# Ranking search program that asks the user for a search query, program quits when an empty string is entered
def ranking_search():
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

    # First let's print some instructions on the Ranking search query for the user:
    print("\n**********************************************************************************************************************")
    print("\n   RELEVANCE RANKING SEARCH:")
    print("\n   Please form the search query in the following manner:")
    print("\n   When searched for one word or multiple different words, separate words with space:")
    print("       word anotherword lastword")
    print("\n   Use quotation marks when searching for intact multi-word phrases (the program only supports bigrams or trigrams):")
    print("       \"New York\"")
    print("\n   Search words can be written in lowercase or uppercase letters, query needs to contain at least one letter.\n")
    print("**********************************************************************************************************************")
    
    while True:
        user_query = str(input("\n\nEnter your query (empty string quits Relevance ranking search): "))
        if user_query == "":
            break
        elif re.fullmatch("\W+", user_query):
            print("\n*** The input was erroneous, cannot show results.\nMake sure your query is typed in as instructed. ***\n")
        elif re.fullmatch("\".+\"", user_query): # Finds exact queries
            user_query_stripped = user_query[1:-1]
            tfv_grams = tfv
            sparse_matrix_grams = sparse_matrix

            # choose the correct length to only match that string
            match len(user_query_stripped.split(" ")):
                case 1:
                    tfv_grams = tfv_1grams
                    sparse_matrix_grams = sparse_matrix_1grams
                case 2:
                    tfv_grams = tfv_2grams
                    sparse_matrix_grams = sparse_matrix_2grams
                case 3:
                    tfv_grams = tfv_3grams
                    sparse_matrix_grams = sparse_matrix_3grams
                case _:
                    print("\n*** The input was erroneous, cannot show results.\nMake sure your query is typed in as instructed.\nWe currently support exact matching only for 1, 2, or 3 words ***\n")
                    continue
            
            query_vec = tfv_grams.transform([user_query_stripped]).tocsc()
            hits = np.dot(query_vec, sparse_matrix_grams)
            try: 
                ranked_scores_and_doc_ids = sorted(zip(np.array(hits[hits.nonzero()])[0], hits.nonzero()[1]), reverse=True)
                # Here we print only the first 10 matching documents:
                print("\n\n______________________________________________________________________________________________________________________")
                print("\nRESULTS:")
                print(f"Query: {user_query}")
                print(f"{len(ranked_scores_and_doc_ids)} matching documents in total.")
                print("______________________________________________________________________________________________________________________")
                doc_number = 1
                for score, i in ranked_scores_and_doc_ids[:10]:
                    print(f"\n\nMatching document #{doc_number}: \n")
                    print("The score for query '{:s}' is {:.4f}\n".format(user_query, score))
                    print_document(documents[i])
                    doc_number += 1
            except IndexError:
                print("\n\n______________________________________________________________________________________________________________________")
                print("\nRESULTS:")
                print(f"Query: {user_query}")
                print(f"Unknown word, no matches found for the search query: {user_query}")
                print("______________________________________________________________________________________________________________________")

        else:
            try:
# commenting out the stemming for now
#                if bool(re.search(r"\".+\"", user_query)) is False:
#                    user_query = stem_que(user_query)
#                else:
#                    None
                query_vec = tfv.transform([user_query]).tocsc()
                hits = np.dot(query_vec, sparse_matrix)
                ranked_scores_and_doc_ids = sorted(zip(np.array(hits[hits.nonzero()])[0], hits.nonzero()[1]), reverse=True)
                # Here we print only the first 10 matching documents:
                print("\n\n______________________________________________________________________________________________________________________")
                print("\nRESULTS:")
                print(f"Query: {user_query}")
                print(f"{len(ranked_scores_and_doc_ids)} matching documents in total.")
                print("______________________________________________________________________________________________________________________")
                doc_number = 1
                for score, i in ranked_scores_and_doc_ids[:10]:
                    print(f"\n\nMatching document #{doc_number}: \n")
                    print("The score for query '{:s}' is {:.4f}\n".format(user_query, score))
                    print_document(documents[i])
                    doc_number += 1
            except SyntaxError:
                print("\n*** The input was erroneous, cannot show results.\nMake sure your query is typed in as instructed. ***\n")
            except IndexError:
                print("\n\n______________________________________________________________________________________________________________________")
                print("\nRESULTS:")
                print(f"Query: {user_query}")
                print(f"Unknown word, no matches found for the search query: {user_query}")
                print("______________________________________________________________________________________________________________________")
    

# The main search engine works here:

def main():
    print("Search engine starts...")

    #Let's do the indexing here:
    

    # Here we'll let the user decide which search engine is going to be used (Boolean or Relevance ranking):
    while True:
        while True:
            print("\n______________________________________________________________________________________________________________________")
            print("\nChoose your search engine:\n1: Boolean search\n2: Relevance ranking search")
            print("______________________________________________________________________________________________________________________")
            engine_choice = str(input("\nEnter your choice by typing 1 or 2 (empty string quits program): "))
            if engine_choice == "":
                print("\nSearch engine closed")
                exit()
            elif engine_choice == "1" or engine_choice == "2":        
                if engine_choice == "1":
                    boolean_search()
                    break
                elif engine_choice == "2":
                    ranking_search()
                    break
            else:
                print("\n*** The input was erroneous, search engine is chosen by only typing 1 or 2. ***\n")

    
#Let's call the main function here:
main()
