import requests
from bs4 import BeautifulSoup as bs
import re
import numpy as np

import matplotlib.pyplot as plt # for graphing

url = "https://www.twtd.co.uk/ipswich-town-fixtures/"

raw = requests.get(url)

soup = bs(raw.text, "html.parser")

pattern = re.compile("\d - \d")

scores = []
for td in soup.find_all("td"):
    if pattern.match(td.text):
        if "cupfix" not in td.previous_sibling.contents[0]['class']:
            scores.append(re.findall("\d", td.text))
            #re.find("

scores=np.array(scores, dtype=int)

points_total = 0
points       = [0]
goals_total  = 0
goals        = [0]
ppg_total    = 0
ppg = [0]
ppg_required = [100/46]

for score in scores:
    if score[0] > score[1]:
        points_total += 3
    elif score[0] == score[1]:
        points_total += 1
    points.append(points_total)
    goals_total += score[0]
    goals.append(goals_total)
    ppg_total = points_total / (len(points)-1)
    ppg.append(ppg_total)
    ppg_required.append((100-points_total)/(46-len(points[1:])))

print(ppg)
print(ppg_required)

home_scores=scores.T[0]
away_scores=scores.T[1]


fig, ax = plt.subplots()

ax.plot(points)
ax.plot(goals)

ax2 = ax.twinx()

ax2.plot(ppg, color="gray")
ax2.plot(ppg_required, "--", color="gray")

ax.set_xlim((0,46))
ax.set_ylim((0,100))

ax2.set_ylim((0,3.5))
plt.show()
