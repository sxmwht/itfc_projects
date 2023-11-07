#!/usr/bin/env python

import imgkit
from get_table import get_table
import pandas as pd

from PIL import Image

class CanvasSection:
    def __init__(self, width, height):
        self.width=width
        self.height=height

class Canvas:
    def divide(self, table):
        self.sections=[]
        for row in tables.rows:
            for cell in tables.cell:
                self.sections.append(CanvasSection(cell.width*self.width, row.height*self.height))

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

    def set_height(self, height):
        print(height)
        self.height=height


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

    def calculate_heights(self):
        total_points = self.rows[0].cells[0].points - self.rows[-1].cells[0].points + len(self.rows)
        for i, row in enumerate(self.rows[:-1]):
            row.set_height((row.cells[0].points-self.rows[i+1].cells[0].points+1)/total_points*100)
        self.rows[-1].height=1/total_points*100

table = get_table()

pt = ProportionalTable()

df = pd.DataFrame({})

for i in range(1, 25):
    pt.add_team(table.loc[i])

#pt.pad()
pt.print()

pt.calculate_heights()

print([p.height for p in pt.rows])



df = pd.DataFrame([[c.team if c is not None else None for c in r.cells] for r in pt.rows])

print(df)

width=300
height=300

img = Canvas(Image.new("RGB", (width,height)))

img.divide(pt)

print(img.sections)




