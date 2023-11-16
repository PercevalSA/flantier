#!/usr/bin/python3
"""
Manage wishes and gifts from google sheets.
Stores every wishes and who is offering what.
"""

import threading
from logging import getLogger

from apiclient.discovery import build

from flantier._settings import SettingsManager
from flantier._users import User, UserManager

logger = getLogger("flantier")


def get_gifts() -> list:
    """Récupère les cadeaux de chaque participant depuis le google doc."""
    google_settings = SettingsManager().get_settings()["google"]
    service = build(
        "sheets",
        "v4",
        credentials=None,
        developerKey=google_settings["api_key"],
    )
    request = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=google_settings["spreadsheet_id"],
            range=google_settings["data_range"],
            majorDimension="COLUMNS",
        )
    )
    spreadsheet = request.execute()
    values = spreadsheet.get("values")

    logger.info("gettings gifts from google sheet")
    logger.debug(values)
    return values


def create_missing_users() -> None:
    """create users present in google sheet but not in database (no telegram account)."""
    gifts = get_gifts()
    user_manager = UserManager()

    for user in gifts[0::2]:
        name = user[0]
        logger.info("checking if %s is missing", name)
        if not user_manager.search_user(name):
            user_manager.add_user(name=name, tg_id=0)


def update_wishes_list() -> None:
    """Met à jour la liste des cadeaux de chaque participant."""
    logger.info("updating wishes list")
    values = get_gifts()
    user_manager = UserManager()

    for column in range(0, len(values), 2):
        name = values[column][0]
        gifts = values[column][1:]
        logger.debug("mise à jour des cadeaux de %s", name)

        user = user_manager.search_user(name)
        if not user:
            pass
        user.wishes = gifts
        user_manager.update_user(user)


def get_wish_list(user: User) -> str:
    """Récupère la liste des souhaits d'un participant avec son nom."""
    return "\n".join(w for w in user.wishes)


def update_gifts_background_task(interval_sec: int = 600) -> None:
    """Update gifts list in background. Function to be run in a thread"""
    ticker = threading.Event()
    while not ticker.wait(interval_sec):
        update_wishes_list()
