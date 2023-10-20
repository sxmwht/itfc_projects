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

##### calculations

games_played = 0
points_total = 0
points       = [0]
goals_total  = 0
goals        = [0]
ppg_total    = 0
ppg = [0]
ppg_required = [100/46]
gpg = 0

# look through each score and create:
# - games played
# - current points total
# - current goals scored
# - a list containing a running total of points
# - a list containing a running total of goals
for score in scores:
    games_played += 1
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

# create other stats 
#   goals per game (gpg) 
gpg=goals_total/games_played
#   games remaining
games_left = 46-games_played
#   PPG over last 10 games
ppg_last_ten = (points_total - points[-11]) / 10

# divide ppg into two lists - one where it contains values >= the corresponding ppg req'd, and one for <
xvals = np.linspace(1,games_played,10000)
ppg_interp = np.interp(xvals, range(1,games_played+1), ppg[1:])
ppgr_interp = np.interp(xvals, range(1,games_played+1), ppg_required[1:])
ppg_gt_ppgr = [entry if entry >= ppgr_interp[index] else None for index,entry in enumerate(ppg_interp)]
ppg_lt_ppgr = [entry if entry <= ppgr_interp[index] else None for index,entry in enumerate(ppg_interp)]


##### graphing


# create the graph object
fig, ax1 = plt.subplots(figsize=(6,5))

# ax1is 1 contains the points and goals, left hand side of the graph
ax1.set_title("Hundred Points, Hundred Goals Tracker 23/24")
ax1.set_ylabel("Points and goals")
ax1.set_xlabel("Games")
ax1.set_xlim((0,46))
ax1.set_ylim((0,122))
ax1.plot(points, color="blue", label="Points")
ax1.plot(goals, label="Goals", color="orange")

ax1.plot(games_played, points_total, ".", color="blue")
ax1.plot(games_played, goals_total, ".", color="orange")
ax1.text(games_played, points_total,     f" {points_total}", c="blue", ha="right", va="bottom")
ax1.text(games_played, goals_total,      f" {goals_total}", c="orange", ha="left", va="top")

# ax1is 2 contains the PPG, RHS of graph
ax2 = ax1.twinx()
ax2.set_ylim((0,3.5*122/140))
ax2.set_ylabel("PPG")
ax2.plot(xvals,[None]+ppg_gt_ppgr[1:], color="green", label="PPG (above required)")
ax2.plot(xvals,[None]+ppg_lt_ppgr[1:], color="red",   label="PPG (below required)")
ax2.plot(ppg_required, "--", color="gray", label="Required PPG")

ax2.plot(games_played, ppg_total, ".", color="green" if ppg_total >= ppg_required[-1] else "red")
ax2.plot(games_played, ppg_required[-1], ".", color="gray")
ax2.text(games_played, ppg_total,        f" {round(ppg_total,2)}", c="green" if ppg_total >= ppg_required[-1] else "red")
ax2.text(games_played, ppg_required[-1], f" {round(ppg_required[-1],2)}", c="gray")

# this is where we plot extra data that we've calculated
#   points trajectory if we continue at current PPG
ax1.plot([games_played,46],[points_total, points_total+(games_left*ppg_total)], linewidth=1, linestyle="dotted", color="blue", label="Points trajectory if current PPG maintained")
#   points trajectory if we continue at PPG of last 10
ax1.plot([games_played,46],[points_total, points_total+(games_left*ppg_last_ten)], linewidth=1, linestyle="dashed", color="blue", label="Points trajectory if PPG of last 10 maintained")
#   goals trajectory if we continue at current GPG
ax1.plot([games_played,46],[goals_total, goals_total+(games_left*gpg)], linewidth=1, linestyle="dotted", color="orange", label="Goals trajectory if current GPG maintained")


h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1[:2]+h2+h1[2:], l1[:2]+l2+l1[2:], loc=4, fontsize=6)

ax1.grid(visible=True, which="both", axis="both")

# plot the 0-100 line
ax1.plot(range(47),np.linspace(0,100,47), "--", color="darkgray", linewidth=0.7)

plt.savefig("hphg.png")
#plt.show()


# upload the image to Thumbsnap and get a URL
url="https://thumbsnap.com/api/upload"
files={
        'key'   : (None, "00044bbe9b8f032c5214bd699910d433"),
        'media' : open("hphg.png", "rb")
}

r=requests.post(url=url, files=files)
img_url=r.json()['data']['media']
print(img_url)
