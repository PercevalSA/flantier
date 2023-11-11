#!/usr/bin/python3
"""COMMANDES ADMINISTRATEUR"""

from logging import getLogger

from telegram import (
    Update,
)
from telegram.ext import (
    CallbackContext,
)

from flantier import _keyboards, _santa
from flantier._roulette import Roulette
from flantier._settings import SettingsManager
from flantier._users import UserManager

logger = getLogger("flantier")


def is_admin(update: Update, context: CallbackContext) -> bool:
    """check if the given telegram id is admin of the bot

    Returns:
        bool: whether the telegram user is admin of the bot or not
    """

    logger.info(
        "%s requested admin rights: %d",
        update.message.from_user.username,
        update.message.from_user.id,
    )

    if (
        update.message.from_user.id
        != SettingsManager().settings["telegram"]["administrator"]
    ):
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="🙅 Petit.e canaillou! Tu ne possèdes pas ce pouvoir.",
        )
        return False

    return True


def open_registrations(update: Update, context: CallbackContext) -> None:
    """Lance la campagne d'inscription. Récupère les résultats de l'année précédente
    comme nouvelles conditions de tirage au sort.
    """
    if not is_admin(update, context):
        return

    Roulette().open_registrations()
    UserManager().update_with_last_year_results()

    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=(
            "🎉 Les inscriptions sont ouvertes 🎉\n"
            "🎅 Vous pouvez désormais vous inscrire en envoyant /participer"
        ),
    )


def close_registrations(update: Update, context: CallbackContext) -> None:
    """Termine la campagne d'inscription."""
    if not is_admin(update, context):
        return

    Roulette().close_registrations()

    context.bot.send_message(
        chat_id=update.message.chat_id,
        text="🙅 Les inscriptions sont fermées 🙅🎁 C'est bientôt l'heure des résultats",
    )


def add_spouse(update: Update, context: CallbackContext) -> None:
    """Ajoute un conjoint à un participant.
    provide names supplier and forbidden recipient else display people keyboard
    """
    if not is_admin(update, context):
        return

    user_manager = UserManager()
    _keyboards.build_exclude_keyboard(update, context, user_manager.users)

    logger.info("message %s", update.message)
    giver = user_manager.search_user("TITI")
    logger.info(giver)

    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=(
            "❓ Qui ne doit pas offrir à qui? "
            "Selectionne la personne a qui iel ne peut pas offrir:"
        ),
    )
    forbidden_recipient = 0

    if user_manager.set_spouse(giver.tg_id, forbidden_recipient):
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="📝 c'est bien noté!",
        )
        logger.info("set spouse %d for %s", forbidden_recipient, giver.name)
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="impossibru")


def process(update: Update, context: CallbackContext) -> None:
    """Lance le tirage au sort et envoie les réponses en message privé."""
    if not is_admin(update, context):
        return

    roulette = Roulette()

    if not roulette.is_ready():
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="⚠️ Les inscriptions ne sont pas encore terminées. ⚠️",
        )
        return

    roulette.tirage()

    # send results to everyone as private message
    user_manager = UserManager()
    for user in user_manager.users:
        if not user.registered:
            pass

        giftee = user_manager.get_user(user.giftee)
        logger.info("send result to %s: giftee is %d", user.name, giftee.tg_id)

        context.bot.send_message(
            user.tg_id,
            text=f"🎅 Youpi tu offres à {giftee.name} 🎁\n",
        )


def update_wishes_list(update: Update, context: CallbackContext) -> None:
    """Met à jour la liste des cadeaux."""
    if _santa.get_cadeaux():
        text = "liste des cadeaux inchangée\n"
    else:
        text = "liste des cadeaux mise à jour\n"

    context.bot.send_message(chat_id=update.message.chat_id, text=text)
    logger.info(text)
