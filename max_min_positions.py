#!/usr/bin/env python

import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import re

# get the upcoming fixtures
fixtures_url = "https://www.bbc.co.uk/sport/football/league-one/scores-fixtures"

data = requests.get(fixtures_url).text
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
    match = [t.string for t in f.find_all(class_=is_team)]
    fixtures.append(match)

# get the current table (thanks Gav)
current_table = pd.read_html("https://www.twtd.co.uk/league-tables/", index_col=0, header=0)[1]
current_table = current_table.drop(["GF", "GA", "W", "D", "L", "GF.1", "GA.1", "W.1", "D.1", "L.1", "Unnamed: 15", "P", "Unnamed: 3", "Unnamed: 9"],axis=1)

# we know team #1 can't go higher
current_table.loc[1, "Max pos"]    = 1
current_table.loc[1, "GD Max pos"] = 1
# look at each row in turn, find max position
for i in range(2,25):
    pts           = current_table.loc[i, "Pts"]
    pts_after_win = current_table.loc[i, "Pts"] + 3
    gd            = current_table.loc[i, "GD"] + 3

    # absolute maximum position, no restrictions. Just 3 points added
    absolute_max_pos   = 25-current_table.sort_values(["Pts", "GD"], ascending=True)["Pts"].searchsorted([pts_after_win] , side="right")
    current_table.loc[i, "Max pos"] = absolute_max_pos

    # find any positions that are only attainable with a GD swing >=4
    gd_table = current_table[current_table.Pts == pts_after_win]
    gd_table_sorted = gd_table.sort_values("GD", ascending=True)
    likely_max_pos = absolute_max_pos + (len(gd_table_sorted) - gd_table_sorted.GD.searchsorted(gd, side="right"))

    current_table.loc[i, "GD Max pos"] = likely_max_pos

    fixtures_copy = [f[:] for f in fixtures]

    # find any impossible positions
    mini_table = current_table[(current_table.Pts > pts) & (current_table.Pts <= pts_after_win)].Team
    teams_on_3 = current_table[(current_table.Pts == pts_after_win)].Team
    max_poss_pos = absolute_max_pos
    for t in (teams_on_3): 
        for match in fixtures_copy:
            if t in match:
                match.remove(t)
                if match != []:
                    if match[0] in mini_table.values:
                        max_poss_pos += 1

    current_table.loc[i, "Max poss pos"] = max_poss_pos


    #print(current_table[current_table.Pts == pts_after_win].Team)


# we know team #24 can't go lower
current_table.loc[24, "Min pos"]    = 24
current_table.loc[24, "GD min pos"] = 24

# minimum position - rudimentary, might not be 100% accurate
# we look at the number of teams below in the league that have a max_pos >= this team's current position
for i in range(1,25):
    current_table.loc[i, "Min pos"] = i + len(current_table.loc[i+1:][current_table.loc[i+1:]["Max pos"] <= i])
    current_table.loc[i, "GD min pos"] = i + len(current_table.loc[i+1:][current_table.loc[i+1:]["GD Max pos"] <= i])

print(current_table)
print(fixtures)

