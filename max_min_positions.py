#!/usr/bin/env python

import requests
import pandas as pd


current_table = pd.read_html("https://www.twtd.co.uk/league-tables/", index_col=0, header=0)[1]

current_table.loc[9, "GD"] = 99

# look at each row in turn, find max position
for i in range(1,25):
    team_name = current_table.loc[i, "Team"]
    points    = current_table.loc[i, "Pts"]
    gd        = current_table.loc[i, "GD"]
    pts_after_win = points + 3
    current_table.loc[i, "Max pos"] = 25-current_table.sort_values(["Pts", "GD"], ascending=True)[["Pts", "GD"]].searchsorted([pts_after_win, gd] , side="right")

print(current_table)

