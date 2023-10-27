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

class Team:
    def __init__(self, pos, entry):
        self.pos = pos
        self.name = entry.Team
        self.points = entry.Pts
        self.gd = entry.GD
        self.is_playing = False
        self.opponent = None

def get_teams_in_reach(team):
    if team.is_playing:
        team.teams_reachable = [t for t in teams[:team.pos-1] if t.points <= team.points + 3]
    else:
        team.teams_reachable = [t for t in teams[:team.pos-1] if t.points == team.points]

def get_teams_easily_in_reach(team):
    if team.is_playing:
        team.teams_easily_reachable = [t for t in team.teams_reachable if t.points == team.points + 3 if t.gd < team.gd + 4]
    else:
        team.teams_easily_reachable = [t for t in team.teams_reachable if t.gd < team.gd + 4]

def find_max_position(team, teams):
    team.max_pos = team.pos
    if team.is_playing:
        team.teams_reachable = [t for t in teams[:team.pos-1] if t.points <= team.points + 3]
        team.max_pos -= len(team.teams_reachable)
    else:
        team.teams_reachable = [t for t in teams[:team.pos-1] if t.points == team.points]
        team.max_pos -= len([t for t in team.teams_reachable if t.is_playing])

def find_min_position(team, teams):
    team.min_pos = team.pos
    team.teams_chasing = [t for t in teams[team.pos:] if t.points >= team.points - 3]
    team.min_pos += len([t for t in team.teams_chasing if t.max_pos <= team.pos])

def find_limiting_fixtures(team, fixtures):
    # a fixture is defined as a team's "limiting fixture" if its result is
    # guaranteed to put a position out of the team's reach. This will occur if
    # BOTH the contestants are 1-3 points ahead of the team AND at least one of
    # the contestants are 3 points ahead of the team
    team.limiting_fixtures = []
    teams_3_ahead      = [t for t in team.teams_reachable if t.points == team.points+3]
    teams_1_to_3_ahead = [t for t in team.teams_reachable if t.points != team.points]
    for f in fixtures:
        if any([True if t in teams_3_ahead else False for t in f]) and all([True if t in teams_1_to_3_ahead else False for t in f]):
            team.limiting_fixtures.append(f)

def get_opponent(team, teams, fixtures):
    for fxt in fixtures:
        if team in fxt:
            if fxt[0] == team:
                team.opponent = fxt[1]
            elif fxt[1] == team:
                team.opponent = fxt[0]
            break

# argument handling
parser = argparse.ArgumentParser(description="Display what a league table could \
        look like after the next round of fixtures")

parser.add_argument('competition', metavar='competition', default='championship',
        choices=["premier-league", "championship", "league-one", "league-two"],
        nargs='?', help="The competition to analyse")

parser.add_argument('-d', '--debug', action="store_true", help="Use the downloaded fixtures/table")

args = parser.parse_args()

# get upcoming fixtures
fixtures_url = f"https://www.bbc.co.uk/sport/football/{args.competition}/scores-fixtures/"

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

# get the current table (thanks Gav)
if args.debug:
    current_table = pd.read_html("debug_table.html", index_col=0, header=0)[1]
else:
    current_table = pd.read_html(f"https://www.twtd.co.uk/league-tables/competition:{args.competition}/", index_col=0, header=0)[1]
current_table = current_table.drop(["GF", "GA", "W", "D", "L", "GF.1", "GA.1", "W.1", "D.1", "L.1", "Unnamed: 15", "P", "Unnamed: 3", "Unnamed: 9"],axis=1)

num_teams = len(current_table.Team)+1

teams = []


for i in range(1,num_teams):
    teams.append(Team(i, current_table.loc[i]))

# replace the names in "fixtures" with their team object
for f in fixtures:
    for i in [0,1]:
        f[i] = [team for team in teams if team.name == f[i]][0]

teams_to_check = [team for match_ in fixtures for team in match_]

for t in teams:
    get_opponent(t, teams, fixtures)

for t in teams:
    t.is_playing = True if t in teams_to_check else False
    get_teams_in_reach(t)
    get_teams_easily_in_reach(t)
    find_limiting_fixtures(t, fixtures)

#for t in teams:
#    find_possible_positions(t, teams)
#
#for t in teams:
#    find_min_position(t, teams)
#
#for t in teams:
#    print(t.name, t.opponent.name if t.opponent is not None else None, " v ".join([team.name for f in t.limiting_fixtures for team in f]), [o.name for o in t.teams_reachable])

