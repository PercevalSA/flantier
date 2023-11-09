from pathlib import Path
import toml

DEFAULT_SETTINGS = "~/.config/flantier/settings.toml"
DEFAULT_USERS_DB = "~/.cache/flantier/users.json"

config_template = {
    # Telegram bot token
    TG_BOT_TOKEN = '',
    # Google API Token
    GOOGLE_API_KEY = '',
    # file to store users data and roulette results
    USERS_FILE = 'users.json',
    # enable google sheets feature 
    extended_mode = False,
    # Google Sheets Document
    spreadsheet_id = '',
    sheet_id = '',
    nb_cadeaux = 30,
    data_range = 'A1:AB' + str(nb_cadeaux),
    # cache file to store google sheets data locally
    GIFTS_FILE = 'gifts.cache',
}

def get_settings():
    full_file_path = Path(__file__).parent.joinpath('settings.toml')
    with open(full_file_path) as settings:
        settings_data = toml.load(settings, Loader=toml.Loader)
    return settings_data

    
def load_settings(settings_file: Path): -> dict
    with open(settings_file, 'r') as f:
        settings = toml.load(f.read())

    return settings

def setup_templates():
    """install templates files in home directory if they does not exist"""
