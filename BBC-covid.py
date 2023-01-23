import nltk, requests
from bs4 import BeautifulSoup
from nltk import word_tokenize

print("Downloading headlines from bbc news about coronavirus.")

url = "https://www.bbc.com/news/coronavirus"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")
titles = soup.find("body").find_all("h3")

print("Printing the 10 latest news: ")

nodup = []
for i in titles :
    clean = str(i.text.strip())
    if clean not in nodup :
        nodup.append(clean)
for j in nodup[:10] :
    print(j)
# Above I created a loop where every result is stripped and then added to a list with no duplicates (nodup)
# If a result is not in the list it will be added to it
# After the nodup list is finished the first ten items within it are printed

