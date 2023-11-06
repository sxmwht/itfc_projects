#k!/usr/bin/env python

import pandas as pd

def get_table():
    # get the current table (thanks Gav)
    current_table = pd.read_html(f"https://www.twtd.co.uk/league-tables/competition:championship/", index_col=0, header=0)[1]

    current_table['GF'] += current_table['GF.1']
    current_table['GA'] += current_table['GA.1']
    current_table['W'] += current_table['W.1']
    current_table['D'] += current_table['D.1']
    current_table['L'] += current_table['L.1']

    current_table  = current_table.drop([ "GF.1", "GA.1", "W.1", "D.1", "L.1", "Unnamed: 15", "Unnamed: 3", "Unnamed: 9"],axis=1)

    return current_table

