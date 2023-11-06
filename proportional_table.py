#!/usr/bin/env python

import imgkit
from get_table import get_table
import pandas as pd


class TableCell:
    def __init__ (self, team):
        self.team = team.Team
        self.points = team.Pts
        self.gd = team.GD
        self.gf = team.GF
        self.width=0


class TableRow:
    def __init__ (self, team=None):
        self.num_teams = 0
        self.cells = []
        if team is not None:
            self.add_cell(team)

    def add_cell(self, team):
        self.cells.append(TableCell(team))
        self.recalculate_cell_widths()

    def recalculate_cell_widths(self):
        total_parts = self.cells[0].gd - self.cells[-1].gd + len(self.cells)
        for i in range(len(self.cells)-1):
            self.cells[i].width = round((self.cells[i].gd-self.cells[i+1].gd+1)/total_parts*100)
        self.cells[-1].width = round(1/total_parts*100)


class ProportionalTable:
    def __init__ (self, team=None):
        self.rows = []
        if team is not None:
            self.rows.append(TableRow(team))

    def add_team(self, team):
        try :
            if team.Pts == self.rows[-1].cells[0].points:
                self.rows[-1].add_cell(team)
            else:
                self.rows.append(TableRow(team))
        except IndexError:
            self.rows.append(TableRow(team))

    def print(self):
        for r in self.rows:
            print([(c.team, c.points, c.width) if c is not None else None for c in r.cells])

    def pad(self):
        for r in self.rows:
            for i in range(len(r.cells), 24):
                r.cells.append(None)

table = get_table()

pt = ProportionalTable()

df = pd.DataFrame({})

for i in range(1, 25):
    pt.add_team(table.loc[i])

#pt.pad()
pt.print()

row_heights = [(pt.rows[i].cells[0].points - pt.rows[i+1].cells[0].points)*16 for i in range(0,len(pt.rows)-1)]

df = pd.DataFrame([[c.team if c is not None else None for c in r.cells] for r in pt.rows])

print(df)

styled_table = df.style.set_table_styles([
    {'selector':''  , 'props':'border-collapse: collapse; font-family:Louis George Cafe; font-size:12px;'},
    {'selector':'tbody tr:nth-child(2n+1)', 'props':'background: #e0e0f0;'},
    {'selector':'tbody tr:nth-child(1)', 'props':f'height: {row_heights[0]}px;'},
    {'selector':'tbody tr:nth-child(2)', 'props':f'height: {row_heights[1]}px;'},
    {'selector':'tbody tr:nth-child(3)', 'props':f'height: {row_heights[2]}px;'},
    {'selector':'tbody tr:nth-child(4)', 'props':f'height: {row_heights[3]}px;'},
    {'selector':'tbody tr:nth-child(5)', 'props':f'height: {row_heights[4]}px;'},
    {'selector':'tbody tr:nth-child(6)', 'props':f'height: {row_heights[5]}px;'},
    {'selector':'tbody tr:nth-child(7)', 'props':f'height: {row_heights[6]}px;'},
    {'selector':'tbody tr:nth-child(8)', 'props':f'height: {row_heights[7]}px;'},
    {'selector':'tbody tr:nth-child(9)', 'props':f'height: {row_heights[8]}px;'},
    {'selector':'tbody tr:nth-child(10)', 'props':f'height: {row_heights[9]}px;'},
    {'selector':'tbody tr:nth-child(11)', 'props':f'height: {row_heights[10]}px;'},
    {'selector':'tbody tr:nth-child(12)', 'props':f'height: {row_heights[11]}px;'},
    {'selector':'tbody tr:nth-child(13)', 'props':f'height: {row_heights[12]}px;'},
    {'selector':'tbody tr:nth-child(14)', 'props':f'height: {row_heights[13]}px;'},
    {'selector':'tbody tr:nth-child(15)', 'props':f'height: {row_heights[14]}px;'},
    {'selector':'tbody tr:nth-child(16)', 'props':f'height: {row_heights[15]}px;'},
    {'selector':'tbody tr:nth-child(17)', 'props':f'height: {row_heights[16]}px;'},
    {'selector':'tbody tr:nth-child(18)', 'props':f'height: {row_heights[17]}px;'},
    {'selector':'tr', 'props':'line-height: 16px'},
    #{'selector':'td', 'props':'white-space: nowrap;padding: 0px 5px 0px 0px;'},
    {'selector':'tbody tr:nth-child(1) td:nth-child(1)', 'props':'colspan: "2";'},
    {'selector':'th', 'props':'padding: 0px 5px;'},
    ])

styled_table.to_html("output.html")
imgkit.from_string(styled_table.to_html(), "table.png", options={'enable-local-file-access':'', 'quality':'100' })

