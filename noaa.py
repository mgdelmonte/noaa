import datetime
import re
import os
import requests
import lxml.html
from six.moves import urllib


def fetch(station="liib", message=None):
    """Fetches all NOAA files, optionally matching station and/or message,
    and saves them in datetime-labeled folder (YYYYMMDDHH).
    :param station: file must have ".{station}." in the URL; default=liib
        station can be a comma-separated list of stations; if blank, gets all stations
    :param message: file must have "/{message}/" in the URL
    """
    # store in a datetime-labeled folder
    dn = datetime.datetime.now().strftime("%Y%m%d%H")
    print("storing NOAA %s messages from %s into %s:" % (message or "all", station or "(all stations)", dn))
    dn = dn + '/'
    # station and message should both be lowercase and delimited for matching in URLs
    if station:
        # station = "." + station.lower() + "."
        if isinstance(station, str):
            station = [i.strip() for i in station.split(',')]
        station = re.compile(r"(?i)\.(%s)\." % "|".join(station).lower())
    if message:
        message = "/" + message.lower() + "/"
    session = requests.session()
    # todo is a list of all the URLs we want to fetch
    todo = ["https://tgftp.nws.noaa.gov/data/raw/"]
    while todo:
        url = todo.pop()
        print(url)
        try:
            page = session.get(url)
        except Exception as e:
            print(e)
            print("unable to get page; skipping")
            continue
        if not page.ok:
            print("got status %s; skipping" % page.status_code)
            continue
        # we got a text file, save it
        if url.endswith(".txt"):
            # verify that it's text
            contenttype = page.headers.get("content-type") or ""
            if 'text/plain' not in contenttype:
                print("got %s instead of text; skipping" % contenttype)
                continue
            # create a filename for it inside the dn folder
            fn = url.replace("https://tgftp.nws.noaa.gov/data/raw/", dn)
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
            if u.endswith("/") and (not message or message in u):
                todo.append(u)
            # if it's a url to a text file (and optionally matches message and station), also put it on the todo list
            elif u.endswith(".txt") and (not station or station.search(u)) and (not message or message in u):
                todo.append(u)



if __name__ == '__main__':
    import fire
    fire.Fire(fetch)
