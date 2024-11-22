"""
Manage wishes and gifts from google sheets.
Stores every wishes and who is offering what.
"""

import threading
from difflib import SequenceMatcher
from itertools import zip_longest
from logging import getLogger
from typing import Optional, Tuple

from apiclient.discovery import build

from flantier._settings import SettingsManager
from flantier._users import User, UserManager, Wish

logger = getLogger("flantier")


def download_google_sheet() -> list:
    """Fetch wishes and comments for all users in the google sheets"""
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


def update_user_wishes(user: User, wishes: list, comments: list) -> None:
    """update all wishes and comments of the user in database.
    Compare currents wishes with the list from google sheet using SequenceMatcher.
    Add new wishes and remove old ones.
    Update the wish with the best match, add new wishes then remove old wishes

    we are using
    https://docs.python.org/2/library/difflib.html#sequencematcher-objects
    but we could use fuzzywuzzy or Levenshtein
    https://pypi.org/project/fuzzywuzzy/
    https://pypi.org/project/Levenshtein/

    Args:
        user (User): user to update
        wishes (list): list of wishes from google sheet
        comments (list): list of comments from google sheet
    """
    logger.debug("updating wishes and comments for %s", user.name)
    logger.debug("content: %s %s", wishes, comments)

    # keep track not to update the same wish multiple times in case of multiple matches
    updated_wishes_indices = set()

    for gs_wish, gs_comment in zip_longest(wishes, comments, fillvalue=""):
        logger.debug("wish: %s", gs_wish)

        best_ratio: float = 0
        new_wish_with_comment: Tuple[Optional[str], Optional[str]] = (None, None)
        wish_to_replace_id = None

        if not gs_wish:
            logger.debug("empty wish in google sheet: %s %s", gs_wish, gs_comment)
            # empty wish in google sheet
            continue

        # for each wish received from google sheet we search for best match in database
        for wish_id, u_wish in enumerate(user.wishes):
            ratio = SequenceMatcher(a=u_wish.wish, b=gs_wish).ratio()
            # similar enough and not already updated
            if (
                ratio > 0.6
                and ratio > best_ratio
                and wish_id not in updated_wishes_indices
            ):
                best_ratio = ratio
                new_wish_with_comment = (gs_wish, gs_comment)
                wish_to_replace_id = wish_id

                logger.debug(
                    'ratio to replace %i by "%s" : %i',
                    wish_to_replace_id,
                    new_wish_with_comment[0],
                    ratio,
                )

        # if a match is found and it hasn't been updated yet
        if wish_to_replace_id is not None:
            assert new_wish_with_comment[0] is not None
            assert new_wish_with_comment[1] is not None
            logger.info(
                'updating wish "%i" with "%s"',
                wish_to_replace_id,
                new_wish_with_comment[0],
            )
            # update wish and comment in database on one go
            (
                user.wishes[wish_to_replace_id].wish,
                user.wishes[wish_to_replace_id].comment,
            ) = new_wish_with_comment
            updated_wishes_indices.add(wish_to_replace_id)
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

    UserManager().update_user(user)


def update_wishes_list() -> None:
    """Met à jour la liste des cadeaux de chaque participant."""
    logger.info("updating wishes list")
    gifts = download_google_sheet()
    user_manager = UserManager()

    for column in range(0, len(gifts), 2):
        name = gifts[column][0]
        wishes = gifts[column][1:]
        comments = gifts[column + 1][1:]

        user = user_manager.search_user(name)
        if not user:
            logger.error("user %s not found", name)

        update_user_wishes(user, wishes, comments)
    logger.info("wishes list updated")


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


# Commands called from keyboards
def set_wish_giver(user_id: int, wish_index: int, giver: int) -> str:
    """Set the giver of a wish so it is reserved and no one else can offer it.

    Args:
        user_id (int): id of the user who will receive the gift
        wish_index (int): index of the wish in the user's wish list
        giver (int): id of the user who offers the gift

    Returns:
        str: text to reply
    """
    logger.info("set wish giver: %s %s %s", user_id, wish_index, giver)
    user_manager = UserManager()
    user = user_manager.get_user(user_id)

    if user_id == giver:
        return (
            "Tu ne peux pas t'offrir un cadeau à toi même."
            "Si tu es Geoffroy contact l'admin."
        )
    if user.wishes[wish_index].giver:
        return (
            "Ce cadeau est déjà offert par "
            + user_manager.get_user(user.wishes[wish_index].giver).name
        )

    user.wishes[wish_index].giver = giver
    user_manager.update_user(user)

    return "Youpi! Tu offres " + user.wishes[wish_index].wish + " à " + user.name


def unset_wish_giver(user_id: int, wish_index: int) -> str:
    """[WIP] Unset the giver of a wish so it is available again.
    TODO finish implementation
    """
    gifts = []
    for user in UserManager().users:
        if user.tg_id == user_id:
            pass

        if user.wishes[wish_index].giver == user_id:
            gifts.append("plop")
            return "Cadeau supprimé"

    return "Cadeau non trouvé"


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
    while True:
        update_wishes_list()
        ticker.wait(interval_sec)
