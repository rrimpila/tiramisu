from flask import Flask, render_template, request

#Initialize Flask instance
app = Flask(__name__)

example_data = [
    {'name': 'Cat sleeping on a bed', 'source': 'cat.jpg'},
    {'name': 'Misty forest', 'source': 'forest.jpg'},
    {'name': 'Bonfire burning', 'source': 'fire.jpg'},
    {'name': 'Old library', 'source': 'library.jpg'},
    {'name': 'Sliced orange', 'source': 'orange.jpg'}
]


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
        for entry in example_data:
            #If an entry name contains the query, add the entry to matches
            if query.lower() in entry['name'].lower():
                matches.append(entry)

    #Render index.html with matches variable
    return render_template('index.html', matches=matches)

