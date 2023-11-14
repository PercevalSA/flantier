#!/usr/bin/python3
"""
Manage wishes and gifts from google sheets.
Stores every wishes and who is offering what.
"""

from logging import getLogger

from apiclient.discovery import build

from flantier._settings import SettingsManager
from flantier._users import UserManager

logger = getLogger("flantier")


def update_user_gifts(user_name: str, gifts: list) -> None:
    """Update user gifts in database."""
    user_manager = UserManager()
    user = user_manager.search_user(user_name)
    if not user:
        return

    user.wishes = gifts
    user_manager.update_user(user)


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
    logger.info(values)
    return values


def update_wishes_list() -> None:
    """Met à jour la liste des cadeaux de chaque participant."""
    values = get_gifts()

    for column in range(0, len(values), 2):
        name = values[column][0]
        gifts = values[column][1:]
        logger.info(name)
        logger.info(gifts)
        update_user_gifts(name, gifts)
        logger.info("mise à jour des cadeaux de %s", name)


def find_wishes(tg_id, name, with_comments=False, table=False):
    """Trouve et retourne la liste de souhaits avec le nom de la personne."""
    participants = UserManager().get_users()
    matches = [qqun for qqun in participants if qqun.name == name]

    if len(matches) == 0:
        if table:
            return []

        return (
            "Je n'ai trouvé personne correspondant à ta recherche. N'oublie pas la"
            " majuscule."
        )

    if matches[0].tg_id == tg_id:
        if table:
            return []

        return (
            "Hop hop hop ! Tu ne peux pas consulter ta propre liste de cadeaux, ça"
            " gacherait la surprise."
        )

    if not table:
        souhaits = ""
        i = 1
        while matches[0].wishes[i] is not None:
            souhaits += str(i) + " : " + matches[0].wishes[i] + "\n"

            if with_comments and matches[0].comments[i] is not None:
                souhaits += "\n" + matches[0].comments[i] + "\n"

            i += 1

        if len(souhaits) == 0:
            souhaits = name + " n'a rien demandé pour Noël :'("

    else:
        souhaits = []
        i = 1
        while matches[0].wishes[i] is not None:
            souhaits.append(matches[0].wishes[i])
            i += 1
    return souhaits
