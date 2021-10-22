#!/usr/bin/env python

import requests
import re

matches = []
raw_data = requests.get("https://www.twtd.co.uk/ipswich-town-fixtures/")
with open("table.txt", "w") as table: 
    points = 0
    goals  = 0
    ppg    = 0
    gpg    = 0
    for r in raw_data.text.splitlines():
        if " - " in r and "cupfix" not in r:
            matches.append(r)

    for l in matches:
        s = re.sub(".*(\d+) - (\d+).*", r"\1 \2", l)
        s = [int(s) for s in s.split(" ")]
        if s[0] > s[1]:
            points += 3
            s.append((points))
        elif s[0] == s[1]:
            points += 1
            s.append(points)
        else:
            s.append(points)
        goals += s[0]
        s.append(goals)

        print(*s, file = table)

    ppg = points/len(matches)
    gpg = goals/len(matches)
    print("ppg {} ({})".format(ppg, ppg*46), "gpg {} ({})".format(gpg, gpg*46))
