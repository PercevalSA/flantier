"""
Manage wishes and gifts from google sheets.
Stores every wishes and who is offering what.
"""

import threading
from difflib import SequenceMatcher
from itertools import zip_longest
from logging import getLogger

from apiclient.discovery import build

from flantier._settings import SettingsManager
from flantier._users import User, UserManager, Wish

logger = getLogger("flantier")


def download_google_sheet() -> list:
    """Récupère les voeux et les commentaires de chaque participant depuis le google doc."""
    logger.info("gettings wishes from google sheet")

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

    logger.info("whishes downloaded")
    logger.debug(values)
    return values


# check if a wish has been modified but is like an existing one
# https://docs.python.org/2/library/difflib.html#sequencematcher-objects
# https://pypi.org/project/fuzzywuzzy/
# https://pypi.org/project/Levenshtein/
def update_user_wishes(user: User, wishes: list, comments: list) -> None:
    """update all wishes and comments of the user in database.
    Compare currents wishes with the list from google sheet using SequenceMatcher.
    Add new wishes and remove old ones.
    Update the wish with the best match, add new wishes then remove old wishes

    Args:
        user (User): user to update
        wishes (list): list of wishes from google sheet
        comments (list): list of comments from google sheet
    """
    logger.info("updating wishes for %s", user.name)
    logger.debug("wishes: %s", wishes)
    logger.debug("comments: %s", comments)

    # keep track in order not to update the same wish multiple times
    # if multiple matches are found
    updated_wishes_indices = set()

    for gs_wish, gs_comment in zip_longest(wishes, comments, fillvalue=""):
        logger.debug("wish: %s", gs_wish)

        best_ratio: float = 0
        new_wish = ""
        new_comment = ""
        to_replace = None

        if not gs_wish:
            logger.debug("empty wish in google sheet: %s %s", gs_wish, gs_comment)
            # empty wish in google sheet
            continue

        # for each wish received from google sheet we search for best match in database
        for idx, u_wish in enumerate(user.wishes):
            ratio = SequenceMatcher(a=u_wish.wish, b=gs_wish).ratio()
            # similar enough and not already updated
            if ratio > 0.6 and ratio > best_ratio and idx not in updated_wishes_indices:
                best_ratio = ratio
                new_wish = gs_wish
                new_comment = gs_comment
                to_replace = u_wish
                to_replace_idx = idx

                logger.debug('ratio: "%s" / "%s": %i', new_wish, to_replace.wish, ratio)

        # if a match is found and it hasn't been updated yet
        if new_wish and to_replace is not None:
            logger.info('updating wish "%s" with "%s"', to_replace.wish, new_wish)
            user.wishes[to_replace_idx].wish = new_wish
            user.wishes[to_replace_idx].comment = new_comment
            updated_wishes_indices.add(to_replace_idx)
        else:
            # no match found or wish already updated
            logger.info("no match found for %s. This is a new one", gs_wish)
            user.wishes.append(Wish(wish=gs_wish, comment=gs_comment))

    # find all missing wishes in gs_wishes to remove them from user wishes
    # updated_wishes_indices = set()
    for u_wish in user.wishes:
        logger.info("cleaning wish %s", u_wish.wish)
        if not u_wish.wish or u_wish.wish not in wishes:
            logger.info("removing wish %s", u_wish.wish)
            user.wishes.remove(u_wish)

    # detect if we have wishes in double in database
    for wish in user.wishes:
        if user.wishes.count(wish) > 1:
            logger.warning("duplicated wish %s", wish.wish)
            user.wishes.remove(wish)

    logger.debug(user.wishes)

    user_manager = UserManager()
    user_manager.update_user(user)


def update_wishes_list() -> None:
    """Met à jour la liste des cadeaux de chaque participant."""
    logger.info("updating wishes list")
    gifts = download_google_sheet()
    user_manager = UserManager()

    for column in range(0, len(gifts), 2):
        name = gifts[column][0]
        wishes = gifts[column][1:]
        comments = gifts[column + 1][1:]
        logger.info("mise à jour des cadeaux de %s: %s", name, wishes)
        logger.info("mise à jour des commentaires de %s: %s", name, comments)

        user = user_manager.search_user(name)
        if not user:
            logger.error("user %s not found", name)

        update_user_wishes(user, wishes, comments)


def get_wish_list(user: User) -> str:
    """Récupère la liste des souhaits d'un participant avec son nom."""
    return "\n".join(w.wish for w in user.wishes)


def get_comment_list(user: User) -> str:
    """Récupère la liste des commentaires d'un participant avec son nom."""
    return "\n".join(w.comment for w in user.wishes)


def get_wishes_and_comments_list(user: User) -> str:
    """Récupère la liste des souhaits et commentaires d'un participant avec son nom."""
    return "\n".join(f"{w.wish} - {w.comment}" for w in user.wishes)


# called by the people inline keyboard
def user_wishes_message(user_name: str) -> str:
    """Generates the text to send as message with all wishes
    from the given user
    """
    wishes = get_wish_list(UserManager().search_user(user_name))
    text = f"🎅 {user_name} voudrait pour Noël:\n" + wishes
    if not wishes:
        text = f"🫥 {user_name} ne veut rien pour Noël"

    return text


def user_comments_message(user_name: str) -> str:
    """Generates the text to send as message with all wishes and associated comments
    from the given user
    """
    user = UserManager().search_user(user_name)
    wishes = get_wishes_and_comments_list(user)

    text = f"🎅 {user_name} voudrait pour Noël:\n" + wishes
    if not wishes:
        text = f"🫥 {user_name} ne veut rien pour Noël"

    return text


def create_missing_users() -> None:
    """create users present in google sheet but not in database (no telegram account)."""
    wishes = download_google_sheet()
    user_manager = UserManager()

    for user in wishes[0::2]:
        name = user[0]
        logger.info("checking if %s is missing", name)
        if not user_manager.search_user(name):
            user_manager.add_user(name=name)


def update_gifts_background_task(interval_sec: int = 600) -> None:
    """Update gifts list in background. Function to be run in a thread"""
    ticker = threading.Event()
    while not ticker.wait(interval_sec):
        update_wishes_list()


# TODO use or remove that function
def compare_wishes(user: User) -> list:
    """for a given user, compare the wish list from from google sheet
    with the one already in database.
    Compareason is based on wish field. We Check if the name of a gift changed slightly
    in order to only update the wish field while keeping the giver field state in database.
    Add new wishes and delete removed ones in google sheet."""
    gifts = download_google_sheet()
    wishes = gifts[gifts.index(user.name) + 1]
    comments = gifts[gifts.index(user.name) + 2]
    logger.info("comparing wishes for %s", user.name)
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
