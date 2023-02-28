import json
import AO3
import time

# Print iterations progress
# from https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()


searchlist = [AO3.Search(language="en", sort_column="kudos_count", revised_at="2022"), AO3.Search(language="en", sort_column="kudos_count", revised_at="2021"), AO3.Search(language="en", sort_column="kudos_count", revised_at="2020"), AO3.Search(language="en", sort_column="kudos_count", revised_at="2019"), AO3.Search(language="en", sort_column="kudos_count", revised_at="2018")] # every item on this list is the same search query (most relevant english works) published on the years between 2022 and 2018
fanfics = []
max_documents_per_year = 100
total_document_count = 0
for search in searchlist: # for every search...
  while search.page <= 5: # look for the works within the first 5 result pages (that'll add up to 100 works per query)
    search.update()
    for result in search.results:
      printProgressBar (total_document_count, max_documents_per_year*len(searchlist))
      if result.nchapters > 0: # if work doesn't have chapters it is restricted and we don't have access
        if not result.chapters:
          time.sleep(2) # requesting this many documents as quickly as possible leads to rate limiting, so we need to take our time
          result.reload() # doesn't load chapters otherwise, it seems
        fanfic = {}
        fanfic['categories'] = result.categories
        fanfic['characters'] = result.characters
        fanfic['fandoms'] = result.fandoms
        fanfic['rating'] = result.rating
        fanfic['relationships'] = result.relationships
        fanfic['tags'] = result.tags
        fanfic['title'] = result.title
        fanfic['warnings'] = result.warnings
        fanfic['id'] = result.id
        fanfic['date_published'] = result.date_published
        if fanfic['date_published']:
          fanfic['date_published'] = fanfic['date_published'].isoformat()

        content = "";
        for chapter in result.chapters:
          if chapter.title:
            content += "<h3>" + chapter.title + "</h3>"
          if chapter.text:
            content += "<p>" + chapter.text + "</p>"
        fanfic['content'] = content
        fanfics.append(fanfic)
        total_document_count += 1
    search.page += 1 # add to the search page count
with open('data/fanfics.json', 'w') as f:
  json.dump(fanfics, f)
print("Done")
