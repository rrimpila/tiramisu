import json
import AO3
import time
import sys
import argparse     

# get year from command line parameter
parser = argparse.ArgumentParser(
    prog='datamine',
    description='Query archive of our own for the top works of the year')
parser.add_argument('-y', '--year', type=int, default=2022)
args = parser.parse_args()

year = str(args.year)

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

fanfics = []
max_documents_per_year = 100
total_document_count = 0
printProgressBar(total_document_count, max_documents_per_year)
search = AO3.Search(language="en", sort_column="kudos_count", revised_at=year)
while total_document_count < max_documents_per_year: # look for the first 100 works, this might go over due to paging from the search
  search.update()
  for result in search.results:
    if result.nchapters > 0: # if work doesn't have chapters it is restricted and we don't have access, so we skip to the next one
      if not result.chapters:
        time.sleep(4) # requesting this many documents as quickly as possible leads to rate limiting, so we need to take our time
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
          content += chapter.title + "\n"
        if chapter.text:
          content += chapter.text + "\n"
      fanfic['content'] = content
      fanfics.append(fanfic)
      total_document_count += 1
      printProgressBar(total_document_count, max_documents_per_year)
  search.page += 1 # add to the search page count

with open(f"data/fanfics{year}.json", 'w', encoding='utf-8') as f:
  json.dump(fanfics, f)
print("Done")
