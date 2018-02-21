# SpiceTools
This repository contains assorted modules for working with MAPPS and
Spice, e.g. manipulating timestamps, analyzing power consumption,
and generating mosaic instructions.

# Feature overview

## Resource analysis of MAPPS datapacks

![](doc/img/power_data_graph.png)

## Generation of JANUS mosaics and PTR requests

One can generate either a full-disk mosaic, or mosaic of the sun-illuminated
surface of a body.

| Python plot | Resulting slew |
| :--------: | :--------: |
| <img src="doc/img/mosaic_14C6_sunside_JANUS.png" width="450"> | ![](doc/img/video_14C6_sunside_JANUS.mp4) |



## Generation of MAJIS slews and PTR requests
Again, the slew can either cover the whole disk, or only the sun-illuminated portion.

| Python plot | Resulting slew |
| :--------: | :--------: |
| <img src="doc/img/scan_22C11_full_MAJIS.png" width="450"> | ![](doc/img/video_22C11_full_MAJIS.mp4) |



## Timestamp processing
Translating between relative and absolute timestamps in MAPPS config files, e.g.
`CLS_APP_CAL +06:28:00` to `2031-04-26T05:08:47Z`, and vice versa.

## Detailed features & how-tos

Example scripts are also available in the [examples](examples/) folder.

## mosaics
This module allows you to automatically create mosaics and scans of either the full
disk of a certain body, or of the sun-illuminated part.

 - **[JANUS mosaics](doc/JANUS_mosaics.md)**
 - **[MAJIS scans](doc/MAJIS_scans.md)**


## timestamps
Process timestamps in ITL files.

 - **[timestamps](doc/timestamps.md)**


## resource_analysis
Perform analysis of consumed resources on a MAPPS scenario.

 - **[resource_analysis](doc/resource_analysis.md)**

## flybys
Analyze various properties of flybys.

 - **[flybys](doc/flybys.md)**
