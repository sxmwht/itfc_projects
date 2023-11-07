#!/usr/bin/env python

import imgkit
from get_table import get_table
import pandas as pd
import re
from PIL import Image

class CanvasSection:
    def __init__(self, width, height, x, y):
        self.w=round(width)
        self.h=round(height)
        self.x = round(x)
        self.y = round(y)

    def fill(self, badge):
        img=Image.open(badge)
        aspect_ratio=self.w/self.h
        if self.w >= self.h:
            box = (0, img.height/2-(img.width/aspect_ratio)/2, img.width, img.height/2+(img.height/aspect_ratio)/2)
        else:
            box = (img.width/2-(img.height*aspect_ratio)/2, 0, img.width/2+(img.height*aspect_ratio)/2, img.height)
        self.img = img.crop(box)


class Canvas:
    def __init__(self, image):
        self.image = image
    def divide(self, table):
        self.sections=[]
        x=0
        y=0
        for row in table.rows:
            for cell in row.cells:
                self.sections.append(CanvasSection(cell.width*self.image.width, row.height*self.image.height, x, y))
                x += cell.width*self.image.width
            y += row.height*self.image.height
            x = 0

    def paint(self):
        for sec in self.sections:
            box = (sec.x, sec.y, sec.x+sec.w, sec.y+sec.h)
            self.image.paste(sec.img.resize((sec.w, sec.h)), box)


class TableCell:
    def __init__ (self, team):
        self.team = re.sub(" ", "-", team.Team.lower())
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
            self.cells[i].width = (self.cells[i].gd-self.cells[i+1].gd+1)/total_parts
        self.cells[-1].width = 1/total_parts

    def set_height(self, height):
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
            row.set_height((row.cells[0].points-self.rows[i+1].cells[0].points+1)/total_points)
        self.rows[-1].height=1/total_points

table = get_table()

pt = ProportionalTable()

df = pd.DataFrame({})


for i in range(1, 25):
    pt.add_team(table.loc[i])

pt.calculate_heights()

df = pd.DataFrame([[c.team if c is not None else None for c in r.cells] for r in pt.rows])

print(df)

width=600
height=800

canvas = Canvas(Image.new("RGB", (width,height)))

canvas.divide(pt)

for section, cell in zip(canvas.sections, [cell for row in pt.rows for cell in row.cells]):
    section.fill(f"./img/logos/large/{cell.team}.png")

canvas.paint()
#canvas.image.show()

row_heights = []
bgs=[]
print(table['Pts'])
total_points = table['Pts'][1]-table['Pts'][24]+len(table['Pts'])
for r in range(1,24):
    row_heights.append((table['Pts'][r]-table['Pts'][r+1]+1)*16)

for r in range(1,25):
    bgs.append(f"/home/sjw/projects/itfc_projects/img/logos/large/{re.sub(' ', '-', table['Team'][r].lower())}.png")
for b in bgs:
    print(b)


print(row_heights)

styled_table = table.style.set_table_styles([
    {'selector':''  , 'props':'border-collapse: collapse; font-family:Louis George Cafe; font-size:12px;'},
    {'selector':'tbody tr:nth-child(2n+1)', 'props':'background: #e0e0f0;'},
    {'selector':'tr', 'props':'line-height: 16px'},
    {'selector':'tr:nth-child(1)', 'props':f'line-height: {row_heights[0]}px; background: url("{bgs[1]}");'},
    {'selector':'tr:nth-child(2)', 'props':f'line-height: {row_heights[1]}px; background: url("{bgs[2]}");'},
    {'selector':'tr:nth-child(3)', 'props':f'line-height: {row_heights[2]}px; background: url("{bgs[3]}");'},
    {'selector':'tr:nth-child(4)', 'props':f'line-height: {row_heights[3]}px; background: url("{bgs[4]}");'},
    {'selector':'tr:nth-child(5)', 'props':f'line-height: {row_heights[4]}px; background: url("{bgs[5]}");'},
    {'selector':'tr:nth-child(6)', 'props':f'line-height: {row_heights[5]}px; background: url("{bgs[6]}");'},
    {'selector':'tr:nth-child(7)', 'props':f'line-height: {row_heights[6]}px; background: url("{bgs[7]}");'},
    {'selector':'tr:nth-child(8)', 'props':f'line-height: {row_heights[7]}px; background: url("{bgs[8]}");'},
    {'selector':'tr:nth-child(9)', 'props':f'line-height: {row_heights[8]}px; background: url("{bgs[9]}");'},
    {'selector':'tr:nth-child(10)', 'props':f'line-height: {row_heights[9]}px; background: url("{bgs[10]}");'},
    {'selector':'tr:nth-child(11)', 'props':f'line-height: {row_heights[10]}px; background: url("{bgs[11]}");'},
    {'selector':'tr:nth-child(12)', 'props':f'line-height: {row_heights[11]}px; background: url("{bgs[12]}");'},
    {'selector':'tr:nth-child(13)', 'props':f'line-height: {row_heights[12]}px; background: url("{bgs[13]}");'},
    {'selector':'tr:nth-child(14)', 'props':f'line-height: {row_heights[13]}px; background: url("{bgs[14]}");'},
    {'selector':'tr:nth-child(15)', 'props':f'line-height: {row_heights[14]}px; background: url("{bgs[15]}");'},
    {'selector':'tr:nth-child(16)', 'props':f'line-height: {row_heights[15]}px; background: url("{bgs[16]}");'},
    {'selector':'tr:nth-child(17)', 'props':f'line-height: {row_heights[16]}px; background: url("{bgs[17]}");'},
    {'selector':'tr:nth-child(18)', 'props':f'line-height: {row_heights[17]}px; background: url("{bgs[18]}");'},
    {'selector':'tr:nth-child(19)', 'props':f'line-height: {row_heights[18]}px; background: url("{bgs[19]}");'},
    {'selector':'tr:nth-child(20)', 'props':f'line-height: {row_heights[19]}px; background: url("{bgs[20]}");'},
    {'selector':'tr:nth-child(21)', 'props':f'line-height: {row_heights[20]}px; background: url("{bgs[21]}");'},
    {'selector':'tr:nth-child(22)', 'props':f'line-height: {row_heights[21]}px; background: url("{bgs[22]}");'},
    {'selector':'tr:nth-child(23)', 'props':f'line-height: {row_heights[22]}px; background: url("{bgs[23]}");'},
    {'selector':'td', 'props':'white-space: nowrap;padding: 0px 5px 0px 0px;'},
    {'selector':'th', 'props':'padding: 0px 5px;'},
  ])

(styled_table.to_html("output.html"))
imgkit.from_string(styled_table.to_html(), "out.png", options={'enable-local-file-access':'', 'quality':'100', 'crop-w':'850', 'crop-y':'23'})
