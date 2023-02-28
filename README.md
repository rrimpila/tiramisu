# Tiramisu
Building an NLP application, a Helsinki University course project by Tiia Poikajärvi, Raine Rimpilä and Minerva Ciccarece.

## Using fan fiction from Archive of Our Own

Archive of Our Own is a site... We query most popular works from the last previous years and provide search options for the content of those works

# Run this application

__NOTE:__ Make sure you are in your `myproject` directory.

Clone this git repository (just use one of the options below!):

```
git clone git@github.com:rrimpila/tiramisu.git # ssh cloning
git https://github.com/rrimpila/tiramisu.git # https cloning
cd tiramisu
```

We will use a virtual environment to contain the project. This way, if you want to export the codebase to a different machine you just have to follow the same instructions to avoid version control problems. If you want to know more about virtual environments and good practices read [this entry](https://docs.python-guide.org/dev/virtualenvs/) - it will save you a lot of headaches...

(NOTE: Instructions for Windows users after this)
Ensure you are in the project folder

__NOTE:__ Make sure you are in your `tiramisu` directory.
And a virtual environment `demoenv`:

```
python3 -m venv demoenv
```

Activate the environment:

```
. demoenv/bin/activate
```

Install requirements for application:

```
pip3 install -r service/requirements.txt
python3 -m spacy download en_core_web_sm
```

__On Windows:__

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

Install requirements for application:

```
pip3 install -r service\requirements.txt
python3 -m spacy download en_core_web_sm

```

The `search_server.py` file is the application's root. This is where all the Flask application goodness will go.  We create an environment variable that points to that file by setting the following environment variables. For your project you can set up that environment variable in your environment's activate script.


In short, show flask which file to run:

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

__On Windows command line__, you can the environment variables with:

```
set FLASK_APP=service\search_server.py
set FLASK_DEMO=True
set FLASK_RUN_PORT=8000
```


FINALLY, typing `flask run` will prompt the virtual environment's Flask package to run an HTTP server using the app object in whatever script the `FLASK_APP` environment variable points to.

So, run the app:

```
flask run
```

and __in your browser__ go to `localhost:8000/` to see the website.
