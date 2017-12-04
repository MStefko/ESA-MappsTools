# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import re
import iso8601
import datetime

RE = re.compile(r'\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}[ Z]')

CA_date = '2030-10-05T02:25:00'
CA = iso8601.parse_date(CA_date)


filepath = r"C:\MAPPS\JUICE_SO\PLANNING\Europa_flyby_MPDR\Europa_flyby_Timeline_MAJIS.itl"
with open(filepath) as f:
    lines = f.readlines()
    
new_lines = []
new_lines.append(f'# CLS_APP_EUR used: {CA_date} -->\n')
for l in lines:
    x = l[:]
    x = x.rstrip()
    if RE.findall(x):
        if len(RE.findall(x))>1:
            raise RuntimeError()
        
        T = RE.findall(x)[0]
        sp = x.split(T)    
        
        
        a = iso8601.parse_date(T)
        if a<CA:
            d = CA - a
            if len(str(d))==7:
                d = "0"+str(d)
            x = sp[0] + f" CLS_APP_EUR -{d} " + sp[1] + f" # {T} "
        else:
            d = a - CA
            if len(str(d))==7:
                d = "0"+str(d)
            x = sp[0] + f" CLS_APP_EUR +{d} " + sp[1] + f" # {T} "
    new_lines.append(x + '\n')
    
w = r"C:\MAPPS\JUICE_SO\PLANNING\Europa_flyby_MPDR\Europa_flyby_Timeline_MAJIS_new.itl"
with open(w, mode='w') as f:
    f.writelines(new_lines)