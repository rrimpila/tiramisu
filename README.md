# Tiramisu
Building an NLP application, a Helsinki University course project by Tiia Poikajärvi, Raine Rimpilä and Minerva Ciccarese.

## Search engine application for fan fiction from Archive of Our Own

[Archive of Our Own](https://archiveofourown.org/) is a website that offers a nonprofit hosting place for fan fiction works. On the website one may read or publish works and tag them according to what relationship category, fandom (fanatic domain, aka the work's source material), rating and content warning(s) they fit best. Additional tags regarding the content of the works may be added freely by the user.
__The Tiramisu search engine__ finds fanworks matching to the user's search query from our defined dataset of fanworks.  
Tiramisu dataset contains a collection of 500 of the most popular fanworks (that is, those that have received the most *kudos* from the users) from works in english that have been published, updated, or edited between between the years 2018 through 2022. The engine also provides different search options for the user in order to search for variety of interesting things within those fanworks.

The two main search options are **boolean** and **relevance ranking** search.
**Boolean** search allows the user to look for both single or multi-word queries along with combinations or exclusions of certain words (i.e. one may ask the search engine to look for works containing the word “cat” but excluding those containing the word “horse”).
Unless otherwise specified by the user, the search will be conducted on all possible inflections of the search query. The search will return all matching documents.
**Relevance** ranking search allows single and multi-word queries as well, but not word combinations nor exclusions. The search will return all matching documents in descending order of relevance. With each work its relevance ranking score will be displayed (that is, how similar the work is to the search query).
Along with either search the user may select certain entities to be highlighted in the results. The highlighted entities will be displayed along with their category (person, date, language, country/city/state).
The search results return not only the first chapter of each work with highlighted entities and query, but also the previously-mentioned achive tags and the dates in which the works have been published, edited and updated.

# How to run this application

### Clone this git repository (just use one of the options below!)

```
git clone git@github.com:rrimpila/tiramisu.git # ssh cloning
git https://github.com/rrimpila/tiramisu.git # https cloning
cd tiramisu
```

We will use a virtual environment to contain the project. This way, if you want to export the codebase to a different machine you just have to follow the same instructions to avoid version control problems. If you want to know more about virtual environments and good practices read [this entry](https://docs.python-guide.org/dev/virtualenvs/) - it will save you a lot of headaches...

### Setting up demoenv

*(__NOTE:__ Scroll down for instructions for Windows users)*  


__NOTE:__ Make sure you are in your `tiramisu` directory.  

Add a virtual environment `demoenv`:

```
python3 -m venv demoenv
```

Activate the environment:

```
. demoenv/bin/activate
```

Install requirements for application (the list of necessary requirements for the app is in the requirements.txt):

```
pip3 install -r service/requirements.txt
python3 -m spacy download en_core_web_sm
```

(When you are finished working in the demoenv, you can deactivate the environment using command ```deactivate```.)  


__Setting up demoenv On Windows:__

Create a project directory:

```
mkdir myproject
cd myproject
```

And a virtual environment `demoenv`:

```
py -3 -m venv demoenv
```

Activate the environment:

```
demoenv\Scripts\activate
```

Install requirements for application (the list of necessary requirements for the app is in the requirements.txt):

```
python3 -m pip install -r service\requirements.txt
python3 -m spacy download en_core_web_sm

```

(When you are finished working in the demoenv, you can deactivate the environment using command ```deactivate```.)  
  
  
### How to run Flask

The `search_server.py` file is the application's root. This is where all the Flask application goodness will go.  We create an environment variable that points to that file by setting the following environment variables. For your project you can set up that environment variable in your environment's activate script.

*(__NOTE:__ Scroll down for instructions for Windows users)*

Show flask which file to run:

```
export FLASK_APP=service/search_server.py
```

Enable development environment to activate interactive debugger and reloader:

```
export FLASK_DEBUG=True
```

Set the port in which to run the application, e.g.:

```
export FLASK_RUN_PORT=8000
```

Here is everything together to simplify your life:
```
export FLASK_APP=service/search_server.py
export FLASK_DEBUG=True
export FLASK_RUN_PORT=8000
```

__On Windows command line__, you can set the environment variables with:

```
set FLASK_APP=service\search_server.py
set FLASK_DEMO=True
set FLASK_RUN_PORT=8000
```
  
  
__FINALLY__, typing `flask run` will prompt the virtual environment's Flask package to run an HTTP server using the app object in whatever script the `FLASK_APP` environment variable points to.

So, run the app:

```
flask run
```

and __in your browser__ go to `localhost:8000/` to see the website.
  
  
## Updating datasets

The repository includes files scraped from Archive of Our Own (metadata and the first chapter of at least 100 fanworks per year, from most relevant works that have been published, updated, or edited between the years 2018 and 2022). This data is expected to remain fairly static, but to update it, you can run the following commands to scrape the files.  
__NOTE:__ This may take a while. The connection may also time out, in that case, run the timed out scraper again.

```
python3 service/datamine.py --year=2018
python3 service/datamine.py --year=2019
python3 service/datamine.py --year=2020
python3 service/datamine.py --year=2021
python3 service/datamine.py --year=2022

```
