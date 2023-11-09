#!/usr/bin/python3

import base64
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

# 96 pages
SITE = "https://zonesons.com"
OSS1 = "/repliques-cultes-de-films-d-espionnage/phrases-cultes-de-oss-117-le-caire-nid-d-espions"
OSS2 = "/repliques-cultes-de-films-d-espionnage/phrases-cultes-de-oss-117-rio-ne-repond-plus"
FILMS = [OSS1, OSS2]
FILENAME = "oss1172.txt"


def url_to_soup(url):
    """Converts an url to a BeautifulSoup object interpeted as html page."""
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urlopen(req) as response:
        if response.status == 404:
            return None
        html_page = response.read()

    return BeautifulSoup(html_page, "html.parser")


for film in FILMS:
    quotes = []

    for page in range(1, 96):
        page_url = f"{SITE}{film}/page-{page}#cu"
        soup = url_to_soup(page_url)

        for quote in soup.findAll("a", {"class": "PostHeader"}):
            quotes.append(SITE + quote.get("href"))

    for quote_url in quotes:
        soup = url_to_soup(quote_url)

        audio = soup.findAll("audio")

        for a in audio:
            mp3 = base64.b64decode(a.get("src")[1:]).decode("utf-8")
            url = f"{SITE}/{mp3}"
            # filename = str(mp3).split("/")[-1]
            filename = str(mp3).rsplit("/", maxsplit=1)[-1]
            print(filename)
            # pylint: disable=W1514
            with open(FILENAME, "a") as file:
                file.write(f"{url}\n")

# to download all files use the following command
# not working (IP ban)
# while read p;
#   do wget -U "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)" "$p";
# done <oss117.txt
# working
# while read p; do open -a Safari "$p"; sleep 5; done <oss1171.txt
