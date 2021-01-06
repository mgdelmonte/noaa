import os
import requests
import lxml.html
from six.moves import urllib

session = requests.session()
done = set()

def get_liib(url):
    done.add(url)
    print(url)
    page = session.get(url)
    if 'liib' in url:
        fn = url.replace("https://tgftp.nws.noaa.gov/data/raw/", "noaa/")
        path = fn.rsplit('/',1)[0]
        if not os.path.exists(path):
            os.makedirs(path)
        with open(fn, 'wb') as f:
            f.write(page.content)
        return
    h = lxml.html.fromstring(page.content, url)
    for e in h.xpath("//a"):
        u = urllib.parse.urljoin(url, e.get("href"))
        if u.startswith("https://tgftp.nws.noaa.gov/data/raw/") and (u.endswith("/") or 'liib' in u) and u not in done:
            get_liib(u)

if __name__ == '__main__':
    get_liib("https://tgftp.nws.noaa.gov/data/raw/")
