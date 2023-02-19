# Flask example

We will use a virtual environment to contain the project. This way, if you want to export the codebase to a different machine you just have to follow the same instructions to avoid version control problems. If you want to know more about virtual environments and good practices read [this entry](https://docs.python-guide.org/dev/virtualenvs/) - it will save you a lot of headaches...

## [Install Flask](https://flask.palletsprojects.com/en/2.2.x/installation/)

(NOTE: Instructions for Windows users after this)
Create a project directory:

```
mkdir myproject
cd myproject
```

And a virtual environment `demoenv`:

```
python3 -m venv demoenv
```

Activate the environment:

```
. demoenv/bin/activate
```

Install Flask:

```
pip install Flask
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
demoenv/Scripts/activate
```

Install requirements:

```
pip3 install -r requirements.txt
python3 -m spacy download en_core_web_sm
```

## Run this Flask example application

__NOTE:__ Make sure you are in your `myproject` directory.

Clone this git repository and move it (just use one of the options below!):

```
git clone git@github.com:jrvc/flask_example.git # ssh cloning
git clone https://github.com/jrvc/flask_example # https cloning
cd flask_example
```

The `flask_demo.py` file is the application's root. This is where all the Flask application goodness will go.  We create an environment variable that points to that file by setting the following environment variables. For your project you can set up that environment variable in your environment's activate script.


In short, show flask which file to run:

```
export FLASK_APP=flaskdemo.py
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
export FLASK_APP=search_server.py
export FLASK_DEBUG=True
export FLASK_RUN_PORT=8000
```

__On Windows command line__, you can the environment variables with:

```
set FLASK_APP=search_server.py
set FLASK_DEMO=True
set FLASK_RUN_PORT=8000
```

__On Windows PowerShell:__

```
$env:FLASK_APP = "flaskdemo.py"
$env:FLASK_DEMO = "True"
$env:FLASK_RUN_PORT = "8000"
```

FINALLY, typing `flask run` will prompt the virtual environment's Flask package to run an HTTP server using the app object in whatever script the `FLASK_APP` environment variable points to.

So, run the app:

```
flask run
```

and __in your browser__ go to `localhost:8000/` to see the website.




## Acknowledgements
Thanks to [Mikko Aulamo](https://researchportal.helsinki.fi/en/persons/mikko-aulamo) for creating the first version of this repo.
