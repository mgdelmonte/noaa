import datetime
import os
import re
import requests
import lxml.html
import urllib
from dateutil.parser import parse


def date_of(s):
    try: return parse(s)
    except: return None


def add_zczc(text):
    return re.sub(r"(\n\n|\A\n*)(\d+)", r"\1ZCZC \2", text)


def fetch(date=None, proxy=None):
    """Fetches all EOAS files from the syn folder, prefixes ZCZCnnn to each message,
    and writes the combined files as YYYY-MM-DDgts.txt.
    :param date: the date to get; defaults to "today"
    :param proxy: optional host:port to use as proxy
    """
    date = date_of(date) or datetime.date.today()
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
        print(url)
        try:
            page = session.get(url)
        except Exception as e:
            print(e)
            print("unable to get page; skipping")
            continue
        if not page.ok:
            print(f"got status {page.status_code}; skipping")
            continue
        # we got a syn file, save it
        if url.endswith(".syn"):
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
                todo.append(u)


if __name__ == '__main__':
    import fire
    fire.Fire(fetch)

