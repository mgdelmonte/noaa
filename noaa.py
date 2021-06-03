import datetime
import glob
import re
import os
import requests
import time
import lxml.html
import urllib
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta


def date_of(s):
    try: return datetime.datetime.strptime(s, '%Y%m%d%H').strftime("%Y%m%d")
    except: return parse(s).strftime("%Y%m%d")


def datehour_of(s):
    try: return datetime.datetime.strptime(s, '%Y%m%d%H').strftime("%Y%m%d%H")
    except: return parse(s).strftime("%Y%m%d%H")


def combine(dir):
    """Combines all files in the directory in a single file named {DATE}gts.txt
    :param dir: the directory to combine; should be named by date or date+hour"""
    dir = str(dir)
    def readfile(fn):
        try:
            with open(fn, "r") as f:
                return "\n".join((fn, f.read().strip()))
        except Exception as e:
            print(f"skipping {fn}: {e}")

    files = glob.glob(f"{dir}/**/*.txt", recursive=True)
    # sort by filename, which is {datehour}-{message}{submessage}{messageid}.{station}..{ext}
    files.sort(key=lambda fn: os.path.split(fn)[1])
    data = "\n\n".join(info for fn in files if (info := readfile(fn)))
    gtsfn = f"{dir[:8]}gts.txt"
    with open(gtsfn, "w") as f:
        f.write(data)
    print(f"wrote {len(data):,} bytes as {gtsfn}")


def fetch(station=None, message=None, datehour=None, dir=None):
    """Fetches all NOAA files, optionally matching station and/or message,
        and saves them in date-labeled folder (YYYYMMDD).
        The files will have the date+hour prepended to their filenames.
    :param station: file must have ".{station}." in the URL; default=liib
        station can be a comma-separated list of stations; defaults to all stations
    :param message: file must have "/{message}/" in the URL
        message can be a comma-separated list of messages; defaults to all messages
    :param datehour: the date or date+hour to fetch; if blank, defaults to "today"
    :param dir: the directory to store data into; defaults to same value as datehour
    """
    datehour = datehour_of(str(datehour)) if datehour else (datetime.datetime.utcnow()-relativedelta(hours=1)).strftime("%Y%m%d%H")
    dir = str(dir or datehour[:8])
    print(f"current time is {str(datetime.datetime.utcnow())[:16]} UTC")
    print(f"storing NOAA %s messages from %s for {datehour[:8]}" % (message or "all", station or "(all stations)"))
    # station and message should both be lowercase and delimited for matching in URLs
    if station:
        if isinstance(station, str):
            station = [i.strip() for i in station.split(',')]
        station = re.compile(r"(?i)\.(%s)\." % "|".join(station).lower())
    if message:
        if isinstance(message, str):
            message = [i.strip() for i in message.split(',')]
        message = re.compile(r"(?i)/(%s)/" % "|".join(message).lower())
    session = requests.session()
    # todo is a list of all the URLs we want to fetch
    todo = ["https://tgftp.nws.noaa.gov/data/raw/"]
    while todo:
        url = todo.pop()
        # print(url)
        try:
            page = session.get(url)
        except Exception as e:
            print(e)
            print("unable to get page; skipping")
            continue
        if not page.ok:
            print(f"got status {page.status_code}; skipping")
            continue
        # we got a text file, save it
        if url.endswith(".txt"):
            # verify that it's text
            contenttype = page.headers.get("content-type") or ""
            if 'text/plain' not in contenttype:
                print(f"got {contenttype} instead of text; skipping")
                continue
            # create a filename for it inside the dn folder, and prepend the modified date+hour
            fn = url.replace("https://tgftp.nws.noaa.gov/data/raw/", dir+"/")
            fn = re.sub("/([^/]+)$", "/"+datehour_of(page.headers['last-modified'])+r'-\1', fn)
            # +datehour_of(page.headers['last-modified'])+'-'
            # the path is the place where the file will be stored on the hard drive
            path = fn.rsplit('/', 1)[0]
            # create the path (the folders) if they don't already exist
            if not os.path.exists(path):
                os.makedirs(path)
            # write the content of the web page as a new file (with filename fn)
            with open(fn, 'wb') as f:
                f.write(page.content)
            continue
        h = lxml.html.fromstring(page.content, url)
        for e in reversed(h.xpath("//a")):
            u = urllib.parse.urljoin(url, e.get("href"))
            # if u isn't longer than where we started, then it's going "up" the tree, so ignore it
            if len(u) <= len(url):
                continue
            # if u ends with a slash, then it's a url to another directory listing, so put it on the todo list
            if u.endswith("/") and (not message or message.search(u)):
                todo.append(u)
            # if it's a url to a text file (and optionally matches message and station and dates), also put it on the todo list
            elif u.endswith(".txt") and (not station or station.search(u)) and (not message or message.search(u)):
                modified = datehour_of(e.xpath("./ancestor::td[1]/following-sibling::td[1]")[0].text)
                # if modified == datehour: # would match date+hour
                if modified[:8] == datehour[:8]: # match only date
                    print(f"{modified} {u}")
                    todo.append(u)
    combine(dir)


def scan(hours=1, station=None, message=None):
    """Perform the "fetch" command continuously at intervals.
    :param interval: the time between fetches, in hours; defaults to 1
    :param station: file must have ".{station}." in the URL; default=liib
        station can be a comma-separated list of stations; defaults to all stations
    :param message: file must have "/{message}/" in the URL
        message can be a comma-separated list of messages; defaults to all messages
    """
    while True:
        next = datetime.datetime.utcnow()+relativedelta(hours=hours)
        fetch(station, message)
        print(f"sleeping {hours} hours until {str(next)[:16]} UTC...")
        time.sleep((next-datetime.datetime.utcnow()).total_seconds())


if __name__ == '__main__':
    import fire
    fire.Fire()

