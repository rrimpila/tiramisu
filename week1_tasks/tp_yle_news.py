# The website I'm using is https://yle.fi/uutiset/tuoreimmat

print("Extracting information from Yle Uutiset \"Tuoreimmat\" website...\n\n")

from urllib import request
url = "https://yle.fi/uutiset/tuoreimmat"
html = request.urlopen(url).read().decode("utf8")


from bs4 import BeautifulSoup
soup = BeautifulSoup(html, "html.parser")


# Finding all headers in the "main" part of the news site:
soup_link_content = soup.find("main", {"id":"yle__contentAnchor"})


# Extracting all h3 headers, which are the headlines, amongst all the headers in "main":
soup_all_headers = soup_link_content.find_all("h3")


print("*** The most recent news headlines from Yle Uutiset: ***\n\n")

# Printing the headlines one by one:
for header in soup_all_headers:
    text = header.find("a")
    print(text.string, "\n")



