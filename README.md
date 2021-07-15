# NOAA data loader

Fetches all NOAA files, optionally matching station and/or message, and saves them in a date-labeled folder (YYYYMMDD).
It also creates a chronological summary file named YYYYMMDD.gts, which contains all messages in order of when they were fetched.

# Installation

- install Python 3
- `pip install -r requirements.txt`

# Running

`python noaa.py --help` for help

# Examples

- `python noaa.py fetch --station=liib` fetches all messages from station "liib"
- `python noaa.py fetch --message=sa,sz` fetches "sa" and "sz" messages from all stations
- `python noaa.py scan --message=sa,sz --station=liib hours=3` fetches "sa" and "sz" messages from station "liib" every three hours

