# flantier
Secret Santa Telegram Bot named Flantier (like in OSS117).
It generates who's offering who, registers which gift is taken and makes jokes

based on https://python-telegram-bot.org and Google Doc API

## quick start

1. clone repo and go in folder
2. edit settings to add your bot key: `vim settings.toml`
3. start bot: `python3 christmas_bot.py settings.toml`

Optionnal: set admin id in `settings.toml` by using the `/register` command while the bot is running and look in `users.json`"

## installation

### Install flantier package and configurations
1. clone repo
1. install flantier with dependencies `sudo python3 -m pip install .`
1. create a bot and get eh API key from the [botfather](https://telegram.me/BotFather)
1. edit configurations to add you bot key and admin telegram id (c.f. quick start): `vim ~/./config/flantier/settings.toml`

### Install flantier user and systemd service
1. create new user: `sudo adduser --shell /bin/noshell --disabled-login flantier`
1. install service file in the right locations `sudo -u flantier mv flantier.service /home/flantier/.config/systemd/user/`
1. launch service `sudo systemctl daemon-reload && sudo systemctl enable flantier && sudo systemctl start flantier`
