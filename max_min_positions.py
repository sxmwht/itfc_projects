#!/usr/bin/env python

import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import re
import sys
import imgkit
import os
import argparse
from itertools import repeat

from datetime import datetime

from get_fixtures import collect_fixtures

def choose_image(team, char):
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
    return ''

class Team:
    def __init__(self, pos, entry):
        self.pos = pos
        self.name = entry.Team
        self.points = int(entry.Pts)
        self.gd = int(entry.GD)
        self.is_playing = False
        self.opponent = None

def get_teams_within_3_above(team, teams):
    if team.is_playing:
        team.teams_reachable = [t for t in teams[:team.pos-1] if t.points <= team.points + 3]
        team.teams_easily_reachable = [t for t in team.teams_reachable if (t.points < team.points + 3 or (t.points == team.points + 3 and t.gd < team.gd + 4))]
    else:
        team.teams_reachable = [t for t in teams[:team.pos-1] if t.points == team.points if t.is_playing]
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

def get_teams_within_3_below(team, teams):
    team.teams_behind = [t for t in teams[team.pos:] if t.points >= team.points - 3 if team in t.teams_reachable]
    team.teams_chasing = [t for t in team.teams_behind if team in t.teams_easily_reachable]


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
                team.is_playing = True
                team.opponent = fxt[1]
                team.is_at_home = True
            elif fxt[1] == team:
                team.is_playing = True
                team.opponent = fxt[0]
                team.is_at_home = False
            break

def run():

    # argument handling
    parser = argparse.ArgumentParser(description="Display what a league table could \
            look like after the next round of fixtures")

    parser.add_argument('competition', metavar='competition', default='championship',
            choices=["premier-league", "championship", "league-one", "league-two"],
            nargs='?', help="The competition to analyse")

    parser.add_argument('-d', '--debug', action="store_true", help="Use the downloaded fixtures/table")

    args = parser.parse_args()

    fixtures = collect_fixtures()

    # get upcoming fixtures

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
        current_table = pd.read_html(f"https://www.twtd.co.uk/league-tables/competition:{args.competition}/", index_col=0)[2]
    current_table = current_table.drop([2,3,4,5,6,7,8,9,10,11,12,13,14,15],axis=1)

    current_table.columns=['Team','GD','Pts']

    num_teams = len(current_table.Team)

    teams = []

    for i in range(1,num_teams):
        teams.append(Team(i, current_table.iloc[i]))

    # replace the names in "fixtures" with their team object
    for f in fixtures:
        for i in [0,1]:
            f[i] = [team for team in teams if team.name == f[i]][0]

    for t in teams:
        t.is_playing = False # will be set by get_opponent if they are playing
        get_opponent(t, teams, fixtures)

    for t in teams:
        get_teams_within_3_above(t,teams)
    for t in teams:
        get_teams_within_3_below(t,teams)
        find_limiting_fixtures(t, fixtures)
        find_helping_fixtures(t, fixtures)
        calculate_possible_positions(t)

    # prints the fixtures
    for f in fixtures:
        print([t.name for t in f])

    df = pd.DataFrame({})

    df[0] = current_table.Team
    for i, team in enumerate(teams):
        df[i+1] = [" "] + list(map(choose_image, repeat(team), team.positions))

    # construct an array of opponents
    df[len(df[0])+1] = [f"<p style='text-align:right'>{p}</p>" for p in current_table.Pts]
    df[len(df[0])+2] = [f"<p style='text-align:right'>{p}</p>" for p in current_table.GD]
    df[len(df[0])+3] = ["Next Fixture"] + [f"<p style='font-style:italic'>vs {team.opponent.name} {'(h)' if team.is_at_home else '(a)'}</p>" if team.opponent is not None else "" for team in teams]

    styled_table = df.style.set_table_styles([
        {'selector':''  , 'props':'border-collapse: collapse; font-family:Louis George Cafe; font-size:12px;'},
        {'selector':'tbody tr:nth-child(1)', 'props':'font-weight:bold;background: #e0e0f0;'},
        {'selector':'tbody tr:nth-child(2n+1)', 'props':'background: #e0e0f0;'},
        {'selector':'tbody tr:nth-child(3)', 'props':'border-bottom: 1px dashed #444444;'},
        {'selector':'tbody tr:nth-child(7)', 'props':'border-bottom: 1px dashed #444444;'},
        {'selector':'tbody tr:nth-child(22)', 'props':'border-bottom: 1px dashed #444444;'},

        {'selector':'tbody tr:nth-child(1)', 'props':'background: #ffffff;'},
        {'selector':'tbody tr:nth-child(2)', 'props':'background: #e0ffe0;'},
        {'selector':'tbody tr:nth-child(3)', 'props':'background: #e0f0e0;'},

        {'selector':'tbody tr:nth-child(4)', 'props':'background: #d5d5ff;'},
        {'selector':'tbody tr:nth-child(5)', 'props':'background: #e0e0f0;'},
        {'selector':'tbody tr:nth-child(6)', 'props':'background: #d5d5ff;'},
        {'selector':'tbody tr:nth-child(7)', 'props':'background: #e0e0f0;'},

        {'selector':'tbody tr:nth-child(23)', 'props':'background: #ffe0f0;'},
        {'selector':'tbody tr:nth-child(24)', 'props':'background: #fffafa;'},
        {'selector':'tbody tr:nth-child(25)', 'props':'background: #ffe0f0;'},

        {'selector':'tr', 'props':'line-height: 16px'},
        {'selector':'td', 'props':'white-space: nowrap;padding: 0px 5px 0px 0px;'},
        {'selector':'th', 'props':'padding: 0px 5px;'},
      ])

    key='''<br><p style='font-family:Louis George Cafe;font-size:12px'>
           <img src="{}"></img> possible move up<br>
           <img src="{}"></img> possible move down <br>
           <img src="{}"></img> possible move up (that requires a GD swing > 3)<br>
           <img src="{}"></img> possible move down (that requires a GD swing > 3)<br>
           <img src="{}"></img> impossible position (due to other fixtures)
           </p>'''.format( os.path.abspath("./img/likely_move.png"),
                           os.path.abspath("./img/likely_move_down.png"),
                           os.path.abspath("./img/unlikely_move.png"),
                           os.path.abspath("./img/unlikely_move_down.png"),
                           os.path.abspath("./img/impossible.png")
                        )

    imgkit.from_string(styled_table.to_html() + key, "out.png", options={'enable-local-file-access':'', 'quality':'100', 'crop-w':'900', 'crop-y':'37'})

if __name__ == "__main__":
    run()
