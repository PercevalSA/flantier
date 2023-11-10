#!/usr/bin/python3
""" Download all OSS 117 audio files from zonesons.com. """

import base64
from pathlib import Path
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from tqdm import tqdm

SITE = "https://zonesons.com"
# pylint: disable=C0301
OSS1 = "/repliques-cultes-de-films-d-espionnage/phrases-cultes-de-oss-117-le-caire-nid-d-espions"
OSS2 = "/repliques-cultes-de-films-d-espionnage/phrases-cultes-de-oss-117-rio-ne-repond-plus"
FILMS = [OSS1, OSS2]


def url_to_soup(url):
    """Converts an url to a BeautifulSoup object interpeted as html page."""
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urlopen(req) as response:
        if response.status == 404:
            return None
        html_page = response.read()

    return BeautifulSoup(html_page, "html.parser")


def list_quotes(_film: str) -> list:
    """List all OSS 117 quotes from zonesons.com."""
    print(f"Analyse des citations de {_film}")
    quotes = []

    # 96 pages
    for page in tqdm(range(1, 97)):
        page_url = f"{SITE}{_film}/page-{page}#cu"
        soup = url_to_soup(page_url)
        for quote in soup.findAll("a", {"class": "PostHeader"}):
            quotes.append(SITE + quote.get("href"))

    return quotes


def get_quotes_url(_film: str, quotes: list):
    """Save all OSS 117 audio files URL from zonesons.com."""
    print("Construction de la liste des URL des citations audios")

    film_name = Path(_film)
    film_name.mkdir(parents=True, exist_ok=True)
    url_file = film_name / "quotes.txt"

    for quote_url in tqdm(quotes):
        soup = url_to_soup(quote_url)
        audio = soup.findAll("audio")

        for a in audio:
            mp3 = base64.b64decode(a.get("src")[1:]).decode("utf-8")
            mp3_url = f"{SITE}/{mp3}"
            # filename = str(mp3).rsplit("/", maxsplit=1)[-1]

            with open(url_file, "a", encoding="utf-8") as file:
                file.write(f"{mp3_url}\n")

    print(f"liste des URL enregistrées dans {url_file}")


# we cannot download files directly because of IP ban
# then to download all files use the following command
# while read p; do open -a Safari "$p"; sleep 5; done <oss1171.txt
#
# this is not working because of IP ban
# while read p;
#   do wget -U "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)" "$p";
# done <oss117.txt

if __name__ == "__main__":
    for film in FILMS:
        get_quotes_url(film.split("/", maxsplit=1)[-1], list_quotes(film))

    print("listing all quotes done. Go into each folder and run the following command:")
    print('while read p; do open -a Safari "$p"; sleep 5; done <quotes.txt')
