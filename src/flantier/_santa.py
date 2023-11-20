#!/usr/bin/python3
"""
Manage wishes and gifts from google sheets.
Stores every wishes and who is offering what.
"""

import threading
from logging import getLogger
from difflib import SequenceMatcher

from apiclient.discovery import build
from itertools import zip_longest
from flantier._settings import SettingsManager
from flantier._users import User, UserManager, Wish
from flantier._commands_admin import send_admin_notification

logger = getLogger("flantier")


def download_gifts() -> list:
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


# check if a wish has been modified but is like an existing one
# https://docs.python.org/2/library/difflib.html#sequencematcher-objects
# https://pypi.org/project/fuzzywuzzy/
# https://pypi.org/project/Levenshtein/
def update_user_wishes(user: User, wishes: list, comments: list) -> None:
    """wish compare function"""
    logger.info("comparing gifts for %s", user.name)
    logger.debug("wishes: %s", wishes)
    logger.debug("comments: %s", comments)

    # FIXME: I'm messed up with naming and order
    # update the wish with the best match
    # add new wishes
    # remove old wishes
    for db_wish, db_comment in zip_longest(wishes, comments, fillvalue=""):
        best_ratio: float = 0
        new_wish = ""

        # search for best match
        for gs_wish in wishes:
            ratio = SequenceMatcher(a=db_wish.wish, b=gs_wish).ratio()
            if ratio > 0.6 and ratio > best_ratio:  # similar enough
                best_ratio = ratio
                new_wish = gs_wish

        # no match found
        if not new_wish:
            logger.info("no match found for %s. This is a new one", db_wish.wish)
            user.wishes.append(Wish(wish=db_wish, comment=c))

            continue

            if 1 > ratio:
                send_admin_notification(f"ratio {ratio}\n{db_wish.wish}\n{gs_wish}")

    tmp_wishes = []
    for w, c in zip_longest(gifts, comments, fillvalue=""):
        logger.info('adding wish "%s" with comment "%s"', w, c)
        wishes.append(Wish(wish=w, comment=c))

    user.wishes = wishes
    user_manager.update_user(user)

    for wish in user.wishes:
        for w in wishes:
            ratio = SequenceMatcher(a=wish.wish, b=w).ratio()
            logger.info("ratio is %s between %s and %s", ratio, wish.wish, w)
            if 1 > ratio >= 0.6:
                send_admin_notification(f"ratio {ratio}\n{wish.wish}\n{w}")


def update_wishes_list() -> None:
    """Met à jour la liste des cadeaux de chaque participant."""
    logger.info("updating wishes list")
    values = download_gifts()
    user_manager = UserManager()

    for column in range(0, len(values), 2):
        name = values[column][0]
        gifts = values[column][1:]
        comments = values[column + 1][1:]
        logger.info("mise à jour des cadeaux de %s: %s", name, gifts)
        logger.info("mise à jour des commentaires de %s: %s", name, comments)

        user = user_manager.search_user(name)
        if not user:
            logger.error("user %s not found", name)

        update_user_wishes(user, gifts, comments)

        # tmp_wishes = []
        # for w, c in zip_longest(gifts, comments, fillvalue=""):
        #     logger.info('adding wish "%s" with comment "%s"', w, c)
        #     wishes.append(Wish(wish=w, comment=c))

        # user.wishes = wishes
        # user_manager.update_user(user)


def get_wish_list(user: User) -> str:
    """Récupère la liste des souhaits d'un participant avec son nom."""
    return "\n".join(w.wish for w in user.wishes)


def get_comment_list(user: User) -> str:
    """Récupère la liste des commentaires d'un participant avec son nom."""
    return "\n".join(w.comment for w in user.wishes)


# called by the people inline keyboard
def user_wishes_message(user_name: str) -> str:
    """Generates the text to send as message with all wishes
    from the given user
    """
    wishes = get_wish_list(UserManager().search_user(user_name))
    text = f"🎅 {user_name} voudrait pour Noël:\n" + wishes
    if not wishes:
        text = f"🎅 {user_name} ne veut rien pour Noël 🫥"

    return text


def user_comments_message(user_name: str) -> str:
    """Generates the text to send as message with all wishes and associated comments
    from the given user
    """
    wishes = get_wish_list(UserManager().search_user(user_name))
    text = f"🎅 {user_name} voudrait pour Noël:\n" + wishes
    if not wishes:
        text = f"🎅 {user_name} ne veut rien pour Noël 🫥"

    return text


def create_missing_users() -> None:
    """create users present in google sheet but not in database (no telegram account)."""
    gifts = download_gifts()
    user_manager = UserManager()

    for user in gifts[0::2]:
        name = user[0]
        logger.info("checking if %s is missing", name)
        if not user_manager.search_user(name):
            user_manager.add_user(name=name, tg_id=0)


def update_gifts_background_task(interval_sec: int = 600) -> None:
    """Update gifts list in background. Function to be run in a thread"""
    ticker = threading.Event()
    while not ticker.wait(interval_sec):
        update_wishes_list()


# FUTURE


def compare_gifts(user: User) -> list:
    """for a given user, compare the wish list from from google sheet
    with the one already in database.
    Compareason is based on wish field. We Check if the name of a gift changed slightly
    in order to only update the wish field while keeping the giver field state in database.
    Add new wishes and delete removed ones in google sheet."""
    gifts = download_gifts()
    wishes = gifts[gifts.index(user.name) + 1]
    comments = gifts[gifts.index(user.name) + 2]
    logger.info("comparing gifts for %s", user.name)
    logger.debug("wishes: %s", wishes)
    logger.debug("comments: %s", comments)

    # check if only a comment has been changed
    for wish in user.wishes:
        if wish.wish in wishes:
            if wish.comment != comments[wishes.index(wish.wish)]:
                logger.info(
                    "comment for %s has been changed: %s",
                    wish.wish,
                    wish.comment,
                )
                wish.comment = comments[wishes.index(wish.wish)]

    for wish in user.wishes:
        for w in wishes:
            logger.info(
                "ratio %s between %s and %s",
                SequenceMatcher(a=wish, b=w).ratio(),
                wish,
                w,
            )

    # # check if a wish has been removed
    # for wish in user.wishes:
    #     if wish.wish not in wishes:
    #         logger.info("wish %s has been removed", wish.wish)
    #         user.wishes.remove(wish)

    # check if a wish has been added
    for wish, comment in zip(wishes, comments):
        if wish not in [w.wish for w in user.wishes]:
            logger.info("wish %s has been added", wish)
            user.wishes.append(Wish(wish=wish, comment=comment))

    return user.wishes
