import os
import requests
import fire
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
    # session is an object that lets you make requests to a webserver
    session = requests.session()
    # todo is a list of all the URLs we want to fetch
    todo = ["https://tgftp.nws.noaa.gov/data/raw/"]
    while todo:
        # take the last url off our todo list
        url = todo.pop()
        # print it
        print(url)
        # fetch the web page at the url
        page = session.get(url)
        # read it using lxml
        h = lxml.html.fromstring(page.content, url)
        # for every link on the page (every <a> element)...
        for e in h.xpath("//a"):
            # ...find its url by joining the page url to the "href" value
            u = urllib.parse.urljoin(url, e.get("href"))
            # if u isn't longer than where we started, then it's going "up" the tree, so ignore it
            if len(u) <= len(url):
                continue
            # if u ends with a slash, then it's a url to another directory listing,
            # so put it on the todo list
            if u.endswith("/"):
                todo.append(u)
            # if it's a url to a text file (and optionally matches message and station),
            # then fetch it and save it
            elif u.endswith(".txt") and (not message or message in u) and (not station or station in u):
                print(u)
                # create a filename for it inside a folder called "noaa"
                fn = u.replace("https://tgftp.nws.noaa.gov/data/raw/", "noaa/")
                # the path is the place where the file will be stored on the hard drive
                path = fn.rsplit('/', 1)[0]
                # create the path (the folders) if they don't already exist
                if not os.path.exists(path):
                    os.makedirs(path)
                # write the content of the web page as a new file (with filename fn)
                with open(fn, 'wb') as f:
                    f.write(page.content)


if __name__ == '__main__':
    import fire
    fire.Fire(fetch)
