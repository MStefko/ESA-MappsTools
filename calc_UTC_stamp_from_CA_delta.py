# -*- coding: utf-8 -*-
"""
Created on Wed Nov  1 09:45:09 2017

@author: Marcel Stefko
"""

from datetime import datetime, timezone, timedelta
datetime.now(timezone.utc).strftime("%Y%m%d")
import iso8601

CA_date = '2031-04-25T22:40:47'
CA = iso8601.parse_date(CA_date)


def get_utc_date(initial_date, delta_seconds):
    final_date = initial_date + timedelta(seconds=delta_seconds)
    return final_date.isoformat()

def parse_delta_input(input_string):
    if len(input_string)==8:
        input_string = "+" + input_string
    t = datetime.strptime(input_string[1:],"%H:%M:%S")
    if input_string[0]=="+":
        delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    elif input_string[0]=="-":
        delta = - timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    else:
        raise ValueError("Incorrect input format, should be: '[+-]HH:MM:SS'.")
    return delta.total_seconds();
    
def delta2utc(input_string):
    print(get_utc_date(CA, parse_delta_input(input_string))[:-6])
    
def utc2delta(input_string):
    T = iso8601.parse_date(input_string)
    if T<CA:
        d = CA - T
        if len(str(d))==7:
            d = "0"+str(d)
        d = "-"+str(d)
    else:
        d = T - CA
        if len(str(d))==7:
            d = "0"+str(d)
        d = "+"+str(d)
    print(d)