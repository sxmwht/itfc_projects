#!/usr/bin/env python

import requests
import pandas as pd


current_table = pd.read_html("https://www.twtd.co.uk/league-tables/", index_col=0, header=0)[1]

#current_table.loc[9, "GD"] = 99

# look at each row in turn, find max position
for i in range(1,25):
    team_name = current_table.loc[i, "Team"]
    points    = current_table.loc[i, "Pts"]
    gd        = current_table.loc[i, "GD"]
    pts_after_win = points + 3

    # absolute maximum position
    absolute_max_pos   = 25-current_table.sort_values(["Pts", "GD"], ascending=True)["Pts"].searchsorted([pts_after_win] , side="right")
    current_table.loc[i, "Max pos"] = absolute_max_pos

    # likely maximum position (without GD swing >= 4)
    likely_max_pos = absolute_max_pos
    print(current_table.loc[likely_max_pos, "GD"].values[0])
    while current_table.loc[likely_max_pos, "GD"].values[0] - gd >= 4:
        likely_max_pos += 1
    current_table.loc[i, "GD max pos"] = likely_max_pos

    
# minimum position - rudimentary, might not be 100% accurate
# we look at the number of teams below in the league that have a max_pos >= this team's current position
for i in range(1,25):
    j=i+1
    while j < 25 and current_table.loc[j, "Max pos"] <= i:
        j += 1

    current_table.loc[i, "Min pos"] = j-1

    # minimum position without a large (>=4) GD swing
    j=i+1
    while j < 25 and current_table.loc[j, "GD max pos"] <= i:
        j += 1

    current_table.loc[i, "GD min pos"] = j-1


print(current_table)

