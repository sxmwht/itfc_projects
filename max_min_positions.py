#!/usr/bin/env python

import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import re
import sys
import imgkit
import os
import argparse
import os

# argument handling
parser = argparse.ArgumentParser(description="Display what a league table could \
        look like after the next round of fixtures")

parser.add_argument('competition', metavar='competition', default='league-one',
        choices=["premier-league", "championship", "league-one", "league-two"],
        nargs='?', help="The competition to analyse")

parser.add_argument('-d', '--debug', action="store_true", help="Use the downloaded fixtures/table")

args = parser.parse_args()

# get upcoming fixtures
fixtures_url = f"https://www.bbc.co.uk/sport/football/{args.competition}/scores-fixtures/2022-02?filter=fixtures"

if (args.debug):
    data = open("debug_fixtures.html").read()
else:
    data = requests.get(fixtures_url).text

soup = bs(data, "html.parser")

def is_match_block(cls):
    return cls and cls == "qa-match-block"

def is_fixture(class_):
    return class_ and class_ == "sp-c-fixture"

def is_team(class_):
    return class_ and re.compile("qa-full-team-name").search(class_)

def collect_fixtures(match_block, fixtures, postponed):
    for f in match_block.find_all(class_=is_fixture):
        match_ = [t.string for t in f.find_all(class_=is_team)]
        if f.find(class_="sp-c-fixture__block sp-c-fixture__block--time gel-brevier"):
            fixtures.append(match_)
        else: 
            for t in match_:
                postponed[t] = f.find(class_="gel-brevier sp-c-fixture__status").text



match_blocks = soup.find_all(class_=is_match_block)
fixtures  = []
postponed = {}
collect_fixtures(match_blocks[0], fixtures, postponed)

try:
    date = match_blocks[0].find("h3").string
    if "Tuesday" in date:
        next_date = match_blocks[1].find("h3").string
        if "Wednesday" in next_date:
            collect_fixtures(match_blocks[1], fixtures)
    elif "Saturday" in date:
        next_date = match_blocks[1].find("h3").string
        if "Sunday" in next_date:
            collect_fixtures(match_blocks[1], fixtures)
except:
    pass

# make names match between BBC sport and TWTD
for f in fixtures:
    for t in f:
        if t == "Brighton & Hove Albion":
            idx = f.index("Brighton & Hove Albion")
            f[idx]= "Brighton and Hove Albion"
        if t == "Milton Keynes Dons":
            idx = f.index("Milton Keynes Dons")
            f[idx]= "MK Dons"

teams_to_check = [team for match_ in fixtures for team in match_]

#try:
#    teams_to_check[teams_to_check.index("Brighton & Hove Albion")] = "Brighton and Hove Albion"
#except:
#    pass
#try:
#    teams_to_check[teams_to_check.index("Milton Keynes Dons")] = "MK Dons"
#except:
#    pass

# get the current table (thanks Gav)
if args.debug:
    current_table = pd.read_html("debug_table.html", index_col=0, header=0)[1]
else:
    current_table = pd.read_html("https://www.twtd.co.uk/league-tables/competition:{}/".format(args.competition), index_col=0, header=0)[1]
current_table = current_table.drop(["GF", "GA", "W", "D", "L", "GF.1", "GA.1", "W.1", "D.1", "L.1", "Unnamed: 15", "P", "Unnamed: 3", "Unnamed: 9"],axis=1)

num_teams = len(current_table.Team)+1

# we know team #1 can't go higher
for i in range(1,num_teams):
    current_table.loc[i, "Max pos"]      = i
    current_table.loc[i, "GD Max pos"]   = i
    current_table.loc[i, "Max poss pos"] = i

# look at each row in turn, find max position
for t in teams_to_check:
    pts           = current_table.loc[current_table.Team == t].Pts.values[0]
    pts_after_win = current_table.loc[current_table.Team == t].Pts.values[0] + 3
    gd            = current_table.loc[current_table.Team == t].GD.values[0]  + 3

    # absolute maximum position, no restrictions. Just 3 points added
    absolute_max_pos   = num_teams-current_table.sort_values(["Pts", "GD"], ascending=True)["Pts"].searchsorted([pts_after_win] , side="right")
    current_table.loc[current_table.Team == t, "Max pos"] = absolute_max_pos

    # find any positions that are only attainable with a GD swing >=4
    gd_table = current_table[current_table.Pts == pts_after_win]
    gd_table_sorted = gd_table.sort_values("GD", ascending=True)
    likely_max_pos = absolute_max_pos + (len(gd_table_sorted) - gd_table_sorted.GD.searchsorted(gd, side="right"))

    current_table.loc[current_table.Team == t, "GD Max pos"] = likely_max_pos

    # find any impossible positions
    fixtures_copy = [f[:] for f in fixtures]
    mini_table = current_table[(current_table.Pts > pts) & (current_table.Pts <= pts_after_win)].Team
    teams_on_3 = current_table[(current_table.Pts == pts_after_win)].Team
    max_poss_pos = absolute_max_pos
    for t3 in (teams_on_3):
        for match_ in fixtures_copy:
            if t3 in match_:
                match_.remove(t3)
                if match_ != []:
                    if match_[0] in mini_table.values:
                        max_poss_pos += 1

    current_table.loc[current_table.Team == t, "Max poss pos"] = max_poss_pos


# minimum position - rudimentary, might not be 100% accurate
# we look at the number of teams below in the league that have a max_pos >= this team's current position
# a team can potentially move down even if they're not playing, so we check all teams
for i in range(1,num_teams):
    current_table.loc[i, "Min pos"] = i + len(current_table.loc[i+1:][current_table.loc[i+1:]["Max pos"] <= i])
    current_table.loc[i, "GD min pos"] = i + len(current_table.loc[i+1:][current_table.loc[i+1:]["GD Max pos"] <= i])

# now we want to create a new dataframe. There will be a column for each team,
# and we iterate through the elements and fill them in with a suitable
# character

graph = []

# priority
# current position
# impossible position

for t in range(1,num_teams):
    graph.append([])
    abs_max_pos    = current_table.loc[t, "Max pos"]
    max_poss_pos   = current_table.loc[t, "Max poss pos"]
    likely_max_pos = current_table.loc[t, "GD Max pos"]
    min_pos        = current_table.loc[t, "Min pos"]
    likely_min_pos = current_table.loc[t, "GD min pos"]

    team_name      = current_table.loc[t, "Team"]

    for pos in range(1,num_teams):
        if pos == t:
            if os.path.exists("./img/logos/{}.png".format(re.sub(" ", "-", team_name).lower())):
                char = '<img src="{}"></img>'.format(os.path.abspath("./img/logos/{}.png".format(re.sub(" ", "-", team_name).lower())))
            else:
                char = '<img src="{}"></img>'.format(os.path.abspath("./img/current.png"))
        elif pos < t:
            if pos < abs_max_pos:
                char = ""
            else:
                if pos < max_poss_pos:
                    char = '<img src="{}"></img>'.format(os.path.abspath("./img/impossible.png"))
                else:
                    if pos == max_poss_pos:
                        if max_poss_pos >= likely_max_pos:
                            char = '<img src="{}"></img>'.format(os.path.abspath("./img/likely_top.png"))
                        else:
                            char = '<img src="{}"></img>'.format(os.path.abspath("./img/unlikely_top.png"))
                    else:
                        if pos < likely_max_pos:
                            char =  '<img src="{}"></img>'.format(os.path.abspath("./img/unlikely_move.png"))
                        else:
                            char =   '<img src="{}"></img>'.format(os.path.abspath("./img/likely_move.png"))
        else:
            if pos > min_pos:
                char = ""
            else:
                if pos == min_pos:
                    if min_pos != likely_min_pos:
                        char = '<img src="{}"></img>' .format(os.path.abspath("./img/unlikely_bottom.png"))
                    else:
                        char = '<img src="{}"></img>' .format(os.path.abspath("./img/likely_bottom.png"))
                else:
                    if pos > likely_min_pos:
                        char = '<img src="{}"></img>'.format(os.path.abspath("./img/unlikely_move_down.png"))
                    else:
                        char = '<img src="{}"></img>'.format(os.path.abspath("./img/likely_move_down.png"))

        graph[-1].append(char)

df = pd.DataFrame({})

df[0] = current_table.Team
for i in range(1,num_teams):
    df[i] = (graph[i-1])

# construct an array of opponents
opponents = []
for t in current_table.Team:
    opp = ""
    if t in postponed.keys():
        opp = postponed[t]
        opponents.append(f"<i><font color = Gray>{opp}</font></i>")
    else:
        for f in fixtures:
            if t in f:
                if f[0] == t:
                    opp = f[1]
                else:
                    opp = f[0]
                break
        if opp != "":
            opponents.append(f"<i><font color = Gray>vs. {opp}</font></i>")
        else:
            opponents.append("")

df["Next Opponents"] = opponents

styled_table = df.style.set_table_styles([
    {'selector':''  , 'props':'border-collapse: collapse; font-family:Louis George Cafe; font-size:12px;'},
    {'selector':'tbody tr:nth-child(2n+1)', 'props':'background: #f0f0f0;'},
    {'selector':'tr', 'props':'line-height: 16px'},
    {'selector':'td', 'props':'padding: 0px 5px 0px 0px;'},
    {'selector':'th', 'props':'padding: 0px 5px;'},
    ])

imgkit.from_string(styled_table.to_html(), "out.png", options={'enable-local-file-access':'', 'quality':'100', 'crop-w':'830', 'crop-y':'23'})

