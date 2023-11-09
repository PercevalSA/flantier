from pathlib import Path
import toml

# config_template = {
#     # Telegram bot token
#     TG_BOT_TOKEN = ''
#     # Google API Token
#     GOOGLE_API_KEY = ''
#     # file to store users data and roulette results
#     USERS_FILE = 'users.json'
#     # enable google sheets feature 
#     extended_mode = False
#     # Google Sheets Document
#     spreadsheet_id = ''
#     sheet_id = ''
#     data_range = 'A1:AB30'
#     # cache file to store google sheets data locally
#     GIFTS_FILE = 'gifts.cache'
# }


class Settings:
    """Singleton class to store settings."""
    
    DEFAULT_SETTINGS = Path("~/.config/flantier/settings.toml")
    DEFAULT_USERS_DB = Path("~/.cache/flantier/users.json")
    
    settings: dict 
    telegram_bot_token: str
    google_api_key: str

    # file to store users data and roulette results
    users_file: Path
    # cache file to store google sheets data locally
    gifts_file: Path
    
    # enable google sheets feature 
    extended_mode: bool = False
    # Google Sheets Document, select the area where to search for whishes in sheet
    spreadsheet_id: str
    sheet_id: str
    data_range: str = 'A1:AB30'

    # singleton
    __instance = None

    def __new__(cls, *args, **kwargs):
        if Settings.__instance is None:
            Settings.__instance = super(Settings, cls).__new__(cls, *args, **kwargs)
        return Settings.__instance


    def get_settings(self):
        full_file_path = Path(__file__).parent.joinpath('settings.toml')
        with open(full_file_path) as settings:
            settings_data = toml.load(settings, Loader=toml.Loader)
        return settings_data

        
    def load_settings(self, settings_file: Path = DEFAULT_SETTINGS):
        with open(self.settings_file, 'r') as f:
            self.settings = toml.load(f.read())

        return self.settings

    def setup_templates(self):
        """install templates files in home directory if they does not exist"""

        DEFAULT_SETTINGS.parents().mkdir(on_error=True)