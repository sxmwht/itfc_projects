#!/usr/bin/env python3

import requests
from datetime import datetime

def collect_fixtures():

    date=datetime.today().strftime('%Y-%m-%d')

    url = "https://www.bbc.co.uk/sport/football/league-one/scores-fixtures"

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB',
        # 'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Origin': 'https://www.efl.com',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Referer': 'https://www.efl.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-GPC': '1',
        # Requests doesn't support trailers
        # 'TE': 'trailers',
    }

    params = {
        'page.size': '12',
        'seasonID': '2025',
        'competitionID': '10',
        'from': date,
        'to': '2026-10-20',
    }

    response = requests.get('https://multi-club-matches.webapi.gc.eflservices.co.uk/v2/matches', params=params, headers=headers)

    hometeams = [m['attributes']['homeTeam']['name'] for m in response.json()['data']]
    awayteams = [m['attributes']['awayTeam']['name'] for m in response.json()['data']]
    fixtures=list([list(m) for m in zip(hometeams,awayteams)])

    return fixtures

if __name__ == "__main__":
    for f in collect_fixtures():
        print(f)


