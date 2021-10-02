import datetime
import os
import re
import requests
import time
import lxml.html
import urllib
import hashlib
from dateutil.parser import parse


md5s = {}

def date_of(s):
    try: return parse(s)
    except: return None


def datehour_of(s):
    try: return datetime.datetime.strptime(s, '%Y%m%d%H')
    except: return parse(s)


def add_zczc(text):
    return re.sub(r"(\n\n|\A\n*)(\d+)", r"\1ZCZC \2", text)


def fetch(date=None, proxy=None, scan=None):
    """Fetches all EOAS files from the syn folder, prefixes ZCZCnnn to each message,
    and writes the combined files as YYYY-MM-DDgts.txt.
    :param date: the date to get; defaults to "today"
    :param proxy: optional host:port to use as proxy
    :param scan: will rescan every <scan> hours for new info
    """
    while scan:
        fetch(date, proxy, scan=False)
        print(f"sleeping {scan} hours")
        time.sleep(scan*3600)
    maxhrs, maxt, maxfile = 0, None, None
    date = date_of(date) or datetime.date.today()
    print("fetching", date)
    fn = date.strftime("%Y-%m-%d-EOAS-GTS.txt")
    if os.path.exists(fn):
        os.remove(fn)
    session = requests.Session()
    if proxy:
        if not re.match("https?://", proxy):
            proxy = f"http://{proxy}"
        session.proxies = dict(http=proxy, https=proxy)
    # todo is a list of all the URLs we want to fetch
    todo = ["http://rawdata.eoas.fsu.edu/syn/"]
    wanted = re.compile(f"{date.strftime('%Y%m%d')}/$|\.syn$")
    while todo:
        url = todo.pop()
        try:
            page = session.get(url)
        except Exception as e:
            print(f"unable to get {url}; skipping")
            continue
        if not page.ok:
            print(f"got status {page.status_code} for {url}; skipping")
            continue
        # we got a syn file, save it
        if url.endswith(".syn"):
            cs = hashlib.md5(page.content).digest()
            old = md5s.get(url)
            if not old:
                print("new", url)
            elif old != cs:
                print("updated", url)
            md5s[url] = cs
            with open(fn, 'a') as f:
                f.write(add_zczc(page.text))
            continue
        h = lxml.html.fromstring(page.content, url)
        for e in reversed(h.xpath("//a")):
            u = urllib.parse.urljoin(url, e.get("href"))
            # if u isn't longer than where we started, then it's going "up" the tree, so ignore it
            if len(u) <= len(url):
                continue
            # if u is wanted, put it on the todo list
            if wanted.search(u):
                if u.endswith('.syn'):
                    t1 = datehour_of(e.text[:10])
                    t2 = datehour_of(e.xpath("./ancestor::td[1]/following-sibling::td[1]")[0].text)
                    hrs = (t2-t1).total_seconds()/3600
                    if hrs > maxhrs:
                        maxhrs, maxt, maxfile = hrs, t2, e.text
                todo.append(u)
    if scan is None:
        print(f'oldest update is {maxfile} updated {maxt}, {maxhrs:0.1f} hours later')


if __name__ == '__main__':
    import fire
    fire.Fire(fetch)

