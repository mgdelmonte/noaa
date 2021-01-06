import os
import requests
import lxml.html
from six.moves import urllib

# session is an object that lets you make requests to a webserver
session = requests.session()

# done is a set that contains all the URLs we've already fetched
done = set()


def get_liib(url):
    """Fetches all files with "liib" in the filename, in the tree starting at <url>,
    and saves them in a folder called "noaa"."""
    # add url to the set of urls we've already done
    done.add(url)
    # print it
    print(url)
    # fetch the web page at the url
    page = session.get(url)
    # if "liib" is in the url, then it's one of the files we want to save
    if 'liib' in url:
        # create a filename for it inside a folder called "noaa"
        fn = url.replace("https://tgftp.nws.noaa.gov/data/raw/", "noaa/")
        # the path is the place where the file will be stored on the hard drive
        path = fn.rsplit('/',1)[0]
        # create the path (the folders) if they don't already exist
        if not os.path.exists(path):
            os.makedirs(path)
        # write the content of the web page as a new file (with filename fn)
        with open(fn, 'wb') as f:
            f.write(page.content)
        # return (end the function, don't do anything else)
        return
    # if "liib" wasn't in the filename, then this page is a directory listing
    # so read it using lxml
    h = lxml.html.fromstring(page.content, url)
    # for every link (every <a> element)...
    for e in h.xpath("//a"):
        # ...find its url by joining the page url to the "href" value
        u = urllib.parse.urljoin(url, e.get("href"))
        # if u is a url to a directory listing or a "liib" file,
        # and if we've not yet done it, then call get_liib on the new url u
        # (This is a "recursive" call to this function.)
        if u.startswith("https://tgftp.nws.noaa.gov/data/raw/") and (u.endswith("/") or 'liib' in u) and u not in done:
            get_liib(u)


if __name__ == '__main__':
    get_liib("https://tgftp.nws.noaa.gov/data/raw/")
