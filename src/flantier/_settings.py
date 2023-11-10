"""Manage settings stored in settings.toml file.
Implement a singleton to access settings everywhere in the code.
"""

import sys
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from shutil import copyfile

import toml

DEFAULT_SETTINGS = Path.home() / ".config/flantier/settings.toml"
DEFAULT_USERS_DB = Path.home() / ".cache/flantier/users.json"
DEFAULT_GIFTS_DB = Path.home() / ".cache/flantier/gifts.json"

logger = getLogger("flantier")


@dataclass
class Settings:
    """Settings data structure."""

    telegram_bot_token: str = ""
    google_api_key: str = ""
    # telegram id of the bot administrator in charge of the roulette
    administrator: int = 0
    # file to store users data and roulette results
    users_file: Path = DEFAULT_USERS_DB
    # cache file to store google sheets data locally
    gifts_file: Path = DEFAULT_GIFTS_DB
    # enable google sheets feature
    extended_mode: bool = False
    # Google Sheets Document, select the area where to search for whishes in sheet
    spreadsheet_id: str = ""
    sheet_id: str = ""
    data_range: str = "A1:AB30"


class SettingsManager:
    """Singleton class to cache settings state and manage settings file."""

    settings = Settings()

    # singleton
    __instance = None

    def __new__(cls, *args, **kwargs):
        if SettingsManager.__instance is None:
            SettingsManager.__instance = super(SettingsManager, cls).__new__(
                cls, *args, **kwargs
            )
        return SettingsManager.__instance

    def get_settings(self) -> Settings:
        """return settings"""
        return self.settings

    # def get_settings(self):
    #     """load settings from file in module folder"""
    #     full_file_path = Path(__file__).parent.joinpath("settings.toml")
    #     with open(full_file_path, "r", encoding="utf-8") as settings:
    #         settings_data = toml.load(settings.read())
    #     return settings_data

    def load_settings(self, settings_file: Path = DEFAULT_SETTINGS) -> Settings:
        """load settings from settings file in default location"""
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                self.settings = toml.load(f.read())
        except FileNotFoundError:
            self.setup_templates(settings_file)
            logger.error(
                "Please configure Flantier Das Geschenk Manager settings at %s",
                settings_file,
            )
            sys.exit(1)

        return self.settings

    def save_settings(self, settings_file: Path = DEFAULT_SETTINGS) -> None:
        """save settings to settings file in default location"""
        with open(settings_file, "w", encoding="utf-8") as f:
            toml.dump(self.settings, f)

    def setup_templates(self, settings_file: Path) -> None:
        """install templates files in home directory if they does not exist"""
        template = Path(__file__).parent.joinpath("settings_template.toml")
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            copyfile(template, settings_file)
        except IOError:
            logger.info("Settings file already in place at %s", DEFAULT_SETTINGS)
