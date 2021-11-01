#!/usr/bin/env python3

from bs4 import BeautifulSoup as bs
import requests
import re

url = "https://www.bbc.co.uk/sport/football/league-one/scores-fixtures"

data = requests.get(url).text
soup = bs(data, "html.parser")

def is_match_block(cls):
    return cls and cls == "qa-match-block"

def is_fixture(class_):
    return class_ == "sp-c-fixture__wrapper"

def is_team(class_):
    return re.compile("qa-full-team-name").search(class_)

upcoming_match_block = soup.find(class_=is_match_block)

fixtures = []
for f in upcoming_match_block.find_all(class_=is_fixture):
    teams = [t.string for t in f.find_all(class_=is_team)]
    print(teams)

