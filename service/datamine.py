import AO3
searchlist = [AO3.Search(language="en", sort_column="kudos_count", revised_at="2022"), AO3.Search(language="en", sort_column="kudos_count", revised_at="2021"), AO3.Search(language="en", sort_column="kudos_count", revised_at="2020"), AO3.Search(language="en", sort_column="kudos_count", revised_at="2019"), AO3.Search(language="en", sort_column="kudos_count", revised_at="2018")] # every item on this list is the same search query (most relevant english works) published on the years between 2022 and 2018
for search in searchlist: # for every search...
  while search.page <= 10: # look for the works within the first ten result pages (that'll add up to 200 works per query)
    search.update()
    for result in search.results:
      print(result)
    search.page += 1 # add to the search page count
print("Done") # will comment this out later
