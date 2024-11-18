# flantier
Secret Santa Telegram Bot named Flantier (like in OSS117).
It generates who's offering who, registers which gift is taken and makes jokes

based on https://python-telegram-bot.org and Google Doc API

## installation

### create bot and get token
1. create a bot and get eh API key from the [botfather](https://telegram.me/BotFather)

### Install flantier directly with pip
1. install flantier `python3 -m pip install "flantier @ git+https://github.com/PercevalSA/flantier"`
1. install service `sudo wget -O /etc/systemd/system/flantier.service https://raw.githubusercontent.com/PercevalSA/flantier/main/flantier.service`
1. edit service to have your username correctly set `sudo vim /etc/systemd/system/flantier.service`
1. start the service `sudo systemctl daemon-reload && sudo systemctl enable flantier && sudo systemctl start flantier`
1. edit configurations to 
    1. add you bot key and admin telegram id (c.f. quick start): `vim ~/.config/flantier/settings.toml`
    1. set administrator id by using the `/register` command while the bot is running and look in `users.json`"

#### Install flantier user and systemd service
You can use a dedicated user to run the bot
1. create new user: `sudo adduser --shell /bin/noshell --disabled-login flantier`
1. install flantier as flantier user `sudo -u flantier python3 -m pip install "flantier @ git+https://github.com/PercevalSA/flantier`
