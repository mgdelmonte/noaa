import os
import requests
import lxml.html
from six.moves import urllib


def fetch(message="liib", station=None):
    """Fetches all NOAA files, optionally matching message and/or station,
    and saves them in a folder called "noaa".
    :param message: file must have ".{message}." in the URL
    :param station: file must have "/{station}/" in the URL
    """
    # message and station should both be lowercase and delimited
    if message:
        message = "."+message.lower()+"."
    if station:
        station = "/"+station.lower()+"/"
    print("searching NOAA %s for %s files:" % (station or "(all stations)", message or "all"))
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
            # create a filename for it inside a folder called "noaa"
            fn = url.replace("https://tgftp.nws.noaa.gov/data/raw/", "noaa/")
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
            if u.endswith("/") and (not station or station in u):
                todo.append(u)
            # if it's a url to a text file (and optionally matches message and station), also put it on the todo list
            elif u.endswith(".txt") and (not message or message in u) and (not station or station in u):
                todo.append(u)



if __name__ == '__main__':
    import fire
    fire.Fire(fetch)
