# -*- coding: utf-8 -*-
"""
Generates stacked power consumption plot from MAPPS datapack export.

Created on Wed Oct 18 16:10:00 2017

@author: Marcel Stefko
"""
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import iso8601

# This information needs to be entered by the user
flyby_name = "14C6"
CA_date = '2031-04-25T22:40:47'
sheet_path = r"C:\MAPPS\JUICE_SO\MAPPS\OUTPUT_DATA\14C6_COMPLETE_test_resources.csv"
TIME_STEP_SECONDS = 20.0
POWER_LIMIT_Wh = 4065.0

# Parse closest approach time
CA = iso8601.parse_date(CA_date)

# Read the MAPPS datapack, skipping the comment rows and the row with units
df = pd.read_csv(sheet_path, skiprows=list(range(22)) + [23], index_col=0)

# Remove all non-power columns from the dataframe
column_names = df.columns[:]
for column_name in column_names:
    if not column_name.startswith("Power"):
        df.drop(column_name, axis=1, inplace=True)


def rename_row_indexes(iso_timestamp):
    """ Reformats the indexes from ISO UTC format to seconds from CA. """
    D = iso8601.parse_date(iso_timestamp)
    if CA>D:
        d = CA - D
        return -(d.days*24 + d.seconds/3600)
    else:
        d = D - CA
        return (d.days*24 + d.seconds/3600)

def rename_columns(col_name):
    """ Strips the string "Power " from column names """
    return col_name[6:]

def get_power_profile():
    """ Returns the black curve for plotting required power profile. """
    x = np.array([-12.0, -12.0, -8.0, -8.0, -0.25, -0.25, 
                  0.25, 0.25, 8.0, 8.0, 12.0, 12.0])
    y = np.array([0.0, 80.0, 80.0, 230.0, 230.0, 360.0,
                  360.0, 230.0, 230.0, 80.0, 80.0, 0.0])
    return (x,y)

# Reformat the timestamps in row indexes
df.rename(rename_row_indexes, inplace=True)
# Strip the string "Power " from column names
df.rename(columns=rename_columns, inplace=True)
# Rename the row index axis
df = df.rename_axis("Time [h]")

# Reorder the instrument columns so that the stacking looks nice
# Note: we are intentionally dropping the HGA and All Instruments columns
# Make sure to name all 10 instruments (and HAA if you have it)!
columns = ['JMAG', 'PEP', '3GM', 'RPWI', 'SWI',
           'RIME', 'JANUS', 'MAJIS', 'GALA', 'UVS']
df = df[columns]

# Create pandas stacked plot and format the axis limits
ax = df.plot.area(stacked=True)
ax.set_xlim([-15.0, 15.0])
ax.set_ylim([0.0, 450.0])
# Plot the black power requirement line
ax.plot(*get_power_profile(), label='LIMIT', c='k', lw=3)
plt.ylabel('Power [W]')
plt.title(f'{flyby_name} - power consumption')
# Reverse the up-down order of labels in the legend because it looks better
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles[::-1], labels[::-1], loc='upper left')
ax.grid()

# Calculate cumulative power consumption:
# - Sum all instruments
# - Do a cumulative sum along the time axis
# - Renormalize by time step to get values in Wh
cumulative_power = df.sum(axis=1).cumsum() / (3600.0/TIME_STEP_SECONDS)

# Plot the cumulative power consumption on the right side
ax2 = ax.twinx()
ax2.set_ylabel('Total consumed power [Wh]')
ax2.set_ylim([0.0, 4700.0])
ax2.set_xlim([-15.0, 15.0])
ax2.plot(cumulative_power.index, cumulative_power, 
         label='CONSUMED', c='g', lw=3)
ax2.plot([-12.0, 12.0], [POWER_LIMIT_Wh]*2, label='LIMIT', c='r', lw=3)
ax2.legend(loc='upper right')

plt.show()

print("Individual instrument consumption:")
for inst in df:
    print(f"{inst}: {df[inst].sum()/(3600.0/TIME_STEP_SECONDS)} Wh")