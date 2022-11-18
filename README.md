# flantier
Secret Santa Telegram Bot named Flantier (like in OSS117). It generates who's offering who, registers which gift is taken and makes jokes

based on https://python-telegram-bot.org and Google Doc API

## quick start

1. clone repo and go in folder
2. edit configs to add your bot key: `vim configs.py`
3. start bot: `python3 christmas-bot.py`

Optionnal: set admin id in `configs.py` by using the `/register` command while the bot is running and look in `users.json`"

## installation

1. clone repo
2. install dependencies: `sudo python3 -m pip install python-telegram-bot google-api-python-client==2.65.0`
3. edit configurations to add you bot key and admin id (c.f. quick start): `vim flantier/configs.json`
4. create new user: `sudo adduser --no-create-home --shell /bin/noshell --disabled-login flantier`
5. install file in the right locations `sudo mv flantier/flantier.service /etc/systemd/sytem/ && sudo mv flantier /srv/`
6. fix rights `sudo chown -R flantier:flantier /srv/flantier && sudo chown root:root /etc/systemd/system/flantier.service`
7. launch service `sudo systemctl daemon-reload && sudo systemctl enable flantier && sudo systemctl start flantier`


## TODO

add audio from :
 - https://zonesons.com/repliques-cultes-de-films-d-espionnage/phrases-cultes-de-oss-117-rio-ne-repond-plus/page-96#cu
 - https://zonesons.com/repliques-cultes-de-films-d-espionnage/phrases-cultes-de-oss-117-le-caire-nid-d-espions/
 