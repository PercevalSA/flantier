#!/usr/bin/python3
"""COMMANDES ADMINISTRATEUR"""

import logging

from telegram import (
    Update,
)
from telegram.ext import (
    CallbackContext,
)

from flantier import _keyboards, _santa
from flantier._roulette import Roulette
from flantier._settings import SettingsManager

logger = logging.getLogger("flantier")


def is_admin(update: Update, context: CallbackContext) -> bool:
    """check if the given telegram id is admin of the bot

    Returns:
        bool: whether the telegram user is admin of the bot or not
    """

    if (
        update.message.from_user.id
        != SettingsManager().settings["telegram"]["administrator"]
    ):
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="🙅 Petit.e canaillou! Tu ne possèdes pas ce pouvoir.",
        )
        logger.info("not an admin")
        return False

    logger.info("admin")
    return True


def open_registrations(update: Update, context: CallbackContext) -> None:
    """Lance la campagne d'inscription."""
    logger.info("open registrations")
    if not is_admin(update, context):
        return

    Roulette().registration = True
    logger.info(f"open registrations: {Roulette().registration}")
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=(
            "🎉 Les inscriptions sont ouvertes 🎉\n"
            "🎅 Vous pouvez désormais vous inscrire en envoyant /participer"
        ),
    )


def close_registrations(update: Update, context: CallbackContext) -> None:
    """Termine la campagne d'inscription."""
    if is_admin(update, context):
        Roulette().registration = False
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=(
                "🙅 Les inscriptions sont fermées 🙅\n"
                "🎁 C'est bientôt l'heure des résultats"
            ),
        )


def add_spouse(update: Update, context: CallbackContext) -> None:
    """Ajoute un conjoint à un participant.
    provide names supplier and forbidden recipient else display people keyboard
    """
    roulette = Roulette()

    _keyboards.build_exclude_keyboard(update, context, roulette.participants)
    supplier = roulette.search_user("TUTU")

    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=(
            "Qui ne doit pas offrir à qui? Selectionne la personne a qui iel ne peut"
            " pas offrir:"
        ),
    )
    forbidden_recipient = 0

    if roulette.exclude(supplier, forbidden_recipient):
        context.bot.send_message(chat_id=update.message.chat_id, text="c'est bon")
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="impossibru")


# TODO generate exlcusion from last year


def process(update: Update, context: CallbackContext) -> None:
    """Lance le tirage au sort et envoie les réponses en message privé."""
    roulette = Roulette()

    if is_admin(update, context):
        if roulette.is_ready():
            # tant que le tirage ne fonctionne pas on relance
            while not roulette.tirage():
                continue

            # on envoie les résultats en message privé
            for user in roulette.participants:
                receiver = roulette.get_user(user["giftee"])
                context.bot.send_message(
                    user["tg_id"],
                    text=f"🎅 Youpi tu offres à : {receiver['name']} 🎁\n",
                )
        else:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="⚠️ Les inscriptions ne sont pas encore terminées. ⚠️",
            )


def update_wishes_list(update: Update, context: CallbackContext) -> None:
    """Met à jour la liste des cadeaux."""
    if _santa.get_cadeaux():
        text = "liste des cadeaux inchangée\n"
    else:
        text = "liste des cadeaux mise à jour\n"

    context.bot.send_message(chat_id=update.message.chat_id, text=text)
    logger.info(text)
