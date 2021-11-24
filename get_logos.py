#!/usr/bin/env python

from bs4 import BeautifulSoup as bs
import requests
import re

soup = bs(requests.get("https://www.logofootball.net/category/england/").text, "html.parser")

def get150(src):
    return src and re.compile("150x150.png").search(src) and not re.compile("HD").search(src) and not re.compile("-1-").search(src)

print(*[t['src'] for t in soup.find_all(src=get150)])
