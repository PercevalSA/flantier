# flantier
Secret Santa Telegram Bot named Flantier (like in OSS117).
It generates who's offering who, registers which gift is taken and makes jokes

based on https://python-telegram-bot.org and Google Doc API

## quick start

1. clone repo and go in folder
2. edit configs to add your bot key: `vim configs.py`
3. start bot: `python3 christmas-bot.py`

Optionnal: set admin id in `configs.py` by using the `/register` command while the bot is running and look in `users.json`"

## installation

1. clone repo
1. install flantier with dependencies `sudo python3 -m pip install .`
1. create a bot and get eh API key from the [botfather](https://telegram.me/BotFather)
1. edit configurations to add you bot key and admin id (c.f. quick start): `vim flantier/configs.json`
1. create new user: `sudo adduser --no-create-home --shell /bin/noshell --disabled-login flantier`
1. install file in the right locations `sudo mv flantier/flantier.service /etc/systemd/sytem/ && sudo mv flantier /srv/`
1. fix rights `sudo chown -R flantier:flantier /srv/flantier && sudo chown root:root /etc/systemd/system/flantier.service`
1. launch service `sudo systemctl daemon-reload && sudo systemctl enable flantier && sudo systemctl start flantier`
