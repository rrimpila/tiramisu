import nltk, re, pprint
from nltk import word_tokenize
from bs4 import BeautifulSoup
from urllib import request
import json
from datetime import datetime
from dateutil import parser

print("Downloading forecast for the next hour:")

# The Finnish meteorological institute site loads the forecast via JSON
# the page source code does not contain it
json_url = "https://www.ilmatieteenlaitos.fi/api/weather/forecasts?place=helsinki"
response_json = request.urlopen(json_url)
json_data = response_json.read().decode('utf8')
data = json.loads(json_data)
if "forecastValues" not in data.keys() or len(data["forecastValues"]) < 1:
  print("Forecast is missing values")
  quit()

# Seems that the JSON might contain the latest passed hour as well, finding the one in the future:
next_forecast = next(obj for obj in data["forecastValues"] if parser.parse(obj["localtime"]) > datetime.now())

# This is useless, the code will fail if localtime is missing
if "localtime" not in next_forecast.keys():
  print("Forecast is missing time")
  quit()

if "Temperature" not in next_forecast.keys():
  print("Forecast is missing temperature")
  quit()
if "FeelsLike" not in next_forecast.keys():
  print("Forecast is missing what temperature feels like")
  quit()
print("The next temperature forecast for {} is {}{}  that will feel like {}{}".format(
      parser.parse(next_forecast["localtime"]).strftime('%H:%M:%S'),
      round(next_forecast["Temperature"], 1),
      u'\u2103',
      round(next_forecast["FeelsLike"], 1),
      u'\u2103'))

# simple website downloading for reference

url = "https://www.ilmatieteenlaitos.fi/saa/helsinki"
response = request.urlopen(url)
html = response.read().decode('utf8')
soup = BeautifulSoup(html, 'html.parser')
print("The main div in the page contains only a comment and will be populated via JS:")
print(soup.find(id="__layout").prettify())
