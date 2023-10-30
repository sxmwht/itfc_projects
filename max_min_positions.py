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

def choose_image(char):
    if char == 'x':
        return '<img src="{}"></img>'.format(os.path.abspath(f"./img/logos/{re.sub(' ', '-', team.name).lower()}.png"))
    if char == 'i':
        return '<img src="{}"></img>'.format(os.path.abspath("./img/impossible.png"))
    if char == 'e':
        return '<img src="{}"></img>'.format(os.path.abspath("./img/likely_move.png"))
    if char == 'r':
        return '<img src="{}"></img>'.format(os.path.abspath("./img/unlikely_move.png"))
    if char == 'b':
        return '<img src="{}"></img>'.format(os.path.abspath("./img/unlikely_move_down.png"))
    if char == 'c':
        return '<img src="{}"></img>'.format(os.path.abspath("./img/likely_move_down.png"))
    if char == 'ut':
        return '<img src="{}"></img>'.format(os.path.abspath("./img/unlikely_top.png"))
    if char == 'lt':
        return '<img src="{}"></img>'.format(os.path.abspath("./img/likely_top.png"))
    if char == 'ld':
        return '<img src="{}"></img>'.format(os.path.abspath("./img/likely_bottom.png"))
    if char == 'ud':
        return '<img src="{}"></img>'.format(os.path.abspath("./img/unlikely_bottom.png"))
    if char == None:
        return ''


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
        team.teams_reachable = [t for t in teams[:team.pos-1] if t.points == team.points if t.is_playing]

def get_teams_easily_in_reach(team):
    if team.is_playing:
        team.teams_easily_reachable = [t for t in team.teams_reachable if (t.points < team.points + 3 or (t.points == team.points + 3 and t.gd < team.gd + 4))]
    else:
        team.teams_easily_reachable = [t for t in team.teams_reachable if t.gd < team.gd + 4 if t.is_playing]

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

def get_teams_behind(team):
    team.teams_behind = [t for t in teams[team.pos:] if t.points >= team.points - 3 if t.is_playing]

def get_teams_chasing(team):
    team.teams_chasing = [t for t in team.teams_behind if (t.points > team.points - 3 or (t.points == team.points - 3 and t.gd > team.gd - 4))]

def find_helping_fixtures(team, fixtures):
    # a fixture is defined as a team's "helping fixture" if its result is
    # guaranteed to ensure a position that the team can't fall to. This will
    # occur if BOTH the contestants are >= 1 points behind the team AND at least
    # one of the contestants are > 1 points behind the team
    team.helping_fixtures = []
    teams_1_to_3_behind = [t for t in team.teams_behind if t.points <= team.points-1]
    teams_2_to_3_behind = [t for t in team.teams_behind if t.points <  team.points-1]
    for f in fixtures:
        if any([True if t in teams_2_to_3_behind else False for t in f]) and all([True if t in teams_1_to_3_behind else False for t in f]):
            team.helping_fixtures.append(f)

def calculate_possible_positions(team):
    # moving upwards
    num_reachable = len(team.teams_reachable)
    num_easily_reachable = len(team.teams_easily_reachable)
    num_impossible = 0
    for f in team.limiting_fixtures:
        num_impossible += 1
        num_reachable -= 1
        if not any([t in team.teams_reachable and t not in team.teams_easily_reachable for t in f]):
            num_easily_reachable -= 1
    team.positions  = ["x" if pos == team.pos-1 else
                       ('lt' if pos == team.pos-1-num_easily_reachable and pos == team.pos-1-num_reachable else
                        ('ut' if pos != team.pos-1-num_easily_reachable and pos == team.pos-1-num_reachable else
                         ('e' if pos >= team.pos-1-num_easily_reachable else
                          ('r' if pos >= team.pos-1-num_reachable else
                           ('i' if pos >= team.pos-1-num_reachable-num_impossible else None))))) for pos in range (0,team.pos)]

    # moving downwards
    num_behind  = len(team.teams_behind)
    num_chasing = len(team.teams_chasing)
    num_impossible = 0
    for f in team.helping_fixtures:
        num_impossible += 1
        num_behind -= 1
        if not any([t in team.teams_behind and t not in team.teams_chasing for t in f]):
            num_chasing -= 1
    team.positions += ['ld' if pos == team.pos-1+num_chasing and pos == team.pos-1+num_behind else
                        ('ud' if pos != team.pos-1+num_chasing and pos == team.pos-1+num_behind else
                         ('c' if pos <= team.pos-1+num_chasing else
                          ('b' if pos <= team.pos-1+num_behind else
                           ('i' if pos <= team.pos-1+num_behind+num_impossible else None)))) for pos in range (team.pos,24)]

def get_opponent(team, teams, fixtures):
    for fxt in fixtures:
        if team in fxt:
            if fxt[0] == team:
                team.opponent = fxt[1]
                team.is_at_home = True
            elif fxt[1] == team:
                team.opponent = fxt[0]
                team.is_at_home = False
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
fixtures_url = f"https://www.bbc.co.uk/sport/football/{args.competition}/scores-fixtures/2023-11"

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
    current_table = pd.read_html(f"https://www.twtd.co.uk/league-tables/competition:{args.competition}/", index_col=0, header=0)[1]
    #current_table = pd.read_html("debug_table.html", index_col=0, header=0)[1]
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

for t in teams:
    get_teams_in_reach(t)
    get_teams_easily_in_reach(t)
    find_limiting_fixtures(t, fixtures)

# prints the fixtures
for f in fixtures:
    print([t.name for t in f])

for t in teams:
    get_teams_behind(t)
    get_teams_chasing(t)
    find_helping_fixtures(t, fixtures)

for t in teams:
    calculate_possible_positions(t)

for t in teams:
    print(t.name, t.positions)

df = pd.DataFrame({})

df[0] = current_table.Team
for i, team in enumerate(teams):
    df[i+1] = list(map(choose_image, team.positions))

# construct an array of opponents
df[len(df[0])+1] = [f"<i><font color = Gray> vs {team.opponent.name} {'(h)' if team.is_at_home else '(a)'}</font></i>" if team.opponent is not None else "" for team in teams]

styled_table = df.style.set_table_styles([
    {'selector':''  , 'props':'border-collapse: collapse; font-family:Louis George Cafe; font-size:12px;'},
    {'selector':'tbody tr:nth-child(2n+1)', 'props':'background: #f0f0f0;'},
    {'selector':'tr', 'props':'line-height: 16px'},
    {'selector':'td', 'props':'white-space: nowrap;padding: 0px 5px 0px 0px;'},
    {'selector':'th', 'props':'padding: 0px 5px;'},
    ])

imgkit.from_string(styled_table.to_html(), "out.png", options={'enable-local-file-access':'', 'quality':'100', 'crop-w':'860', 'crop-y':'23'})

