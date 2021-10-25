#!/usr/bin/env python

import requests
import pandas as pd


current_table = pd.read_html("https://www.twtd.co.uk/league-tables/", index_col=0, header=0)[1]

current_table = current_table.drop(["GF", "GA", "W", "D", "L", "GF.1", "GA.1", "W.1", "D.1", "L.1", "Unnamed: 15", "P", "Unnamed: 3", "Unnamed: 9"],axis=1)

# we know team #1 can't go higher
current_table.loc[1, "Max pos"]    = 1
current_table.loc[1, "GD Max pos"] = 1
# look at each row in turn, find max position
for i in range(2,25):
    pts_after_win = current_table.loc[i, "Pts"] + 3
    gd            = current_table.loc[i, "GD"] + 3

    # absolute maximum position
    absolute_max_pos   = 25-current_table.sort_values(["Pts", "GD"], ascending=True)["Pts"].searchsorted([pts_after_win] , side="right")
    current_table.loc[i, "Max pos"] = absolute_max_pos

    gd_table = current_table[current_table.Pts == pts_after_win].sort_values("GD", ascending=True)
    likely_max_pos = absolute_max_pos + (len(gd_table) - gd_table.GD.searchsorted(gd, side="right"))

    current_table.loc[i, "GD Max pos"] = likely_max_pos

# we know team #24 can't go lower
current_table.loc[24, "Min pos"]    = 24
current_table.loc[24, "GD min pos"] = 24

# minimum position - rudimentary, might not be 100% accurate
# we look at the number of teams below in the league that have a max_pos >= this team's current position
for i in range(1,25):
    current_table.loc[i, "Min pos"] = i + len(current_table.loc[i+1:][current_table.loc[i+1:]["Max pos"] <= i])
    current_table.loc[i, "GD min pos"] = i + len(current_table.loc[i+1:][current_table.loc[i+1:]["GD Max pos"] <= i])

print(current_table)

