#!/usr/bin/env python

import pandas as pd
import imgkit

from get_table import get_table

current_table = get_table()

ga_table = current_table.sort_values(["GA", "Pts"], ascending=[True, False])

styled_table = ga_table.style.set_table_styles([
    {'selector':''  , 'props':'border-collapse: collapse; font-family:Louis George Cafe; font-size:12px;'},
    {'selector':'tbody tr:nth-child(2n+1)', 'props':'background: #e0e0f0;'},
    {'selector':'tr', 'props':'line-height: 16px'},
    {'selector':'td', 'props':'white-space: nowrap;padding: 0px 5px 0px 0px;'},
    {'selector':'th', 'props':'padding: 0px 5px;'},
    ])

imgkit.from_string(styled_table.to_html(), "out.png", options={'enable-local-file-access':'', 'quality':'100', 'crop-w':'350', 'crop-y':'23'})

