#!/usr/bin/python3

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import base64

# 96 pages
site = "https://zonesons.com"
oss1 = "/repliques-cultes-de-films-d-espionnage/phrases-cultes-de-oss-117-le-caire-nid-d-espions"
oss2 = "/repliques-cultes-de-films-d-espionnage/phrases-cultes-de-oss-117-rio-ne-repond-plus"
films = [oss1, oss2]

for film in films:
    quotes = []

    for page in range(1, 96):
        page_url = f"{site}{film}/page-{page}#cu"
        req = Request(page_url, headers={'User-Agent': 'Mozilla/5.0'})
        html_page = urlopen(req).read()
        soup = BeautifulSoup(html_page, 'html.parser')
        for quote in soup.findAll('a', {'class': "PostHeader"}):
            quotes.append(site + quote.get('href'))

    for quote in quotes:
        req = Request(quote, headers={'User-Agent': 'Mozilla/5.0'})
        html_page = urlopen(req).read()

        soup = BeautifulSoup(html_page, 'html.parser')
        audio = soup.findAll('audio')

        for a in audio:
            mp3 = base64.b64decode(a.get('src')[1:]).decode("utf-8")
            url = f"{site}/{mp3}"
            filename = str(mp3).split('/')[-1]
            print(filename)

            with open('oss117.txt', 'a') as file:
                file.write(f"{url}\n")

# to download all files use the following command in a loop
# wget -U "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)" ${url}
