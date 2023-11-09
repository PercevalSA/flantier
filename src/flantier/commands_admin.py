#!/usr/bin/python3
"""COMMANDES ADMINISTRATEUR"""

import logging

import configs
import keyboards
import santa
from roulette import Roulette
from telegram import (
    Update,
)
from telegram.ext import (
    CallbackContext,
)

logger = logging.getLogger("flantier")


def is_admin(update: Update, context: CallbackContext) -> bool:
    """check if the given telegram id is admin of the bot

    Returns:
        bool: whether the telegram user is admin of the bot or not
    """
    if update.message.from_user.id != configs.admin:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="🙅 Petit.e canaillou! Tu ne possèdes pas ce pouvoir.",
        )
        return False

    return True


def open_registrations(update: Update, context: CallbackContext):
    """Lance la campagne d'inscription."""
    if is_admin(update, context):
        Roulette().inscriptions_open = True
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=(
                "🎉 Les inscriptions sont ouvertes 🎉\n"
                "🎅 Vous pouvez désormais vous inscrire en envoyant /participer"
            ),
        )


def close_registrations(update: Update, context: CallbackContext):
    """Termine la campagne d'inscription."""
    if is_admin(update, context):
        Roulette().inscriptions_open = False
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=(
                "🙅 Les inscriptions sont fermées 🙅\n"
                "🎁 C'est bientôt l'heure des résultats"
            ),
        )


def add_spouse(update: Update, context: CallbackContext):
    """Ajoute un conjoint à un participant.
    provide names supplier and forbidden recipient else display people keyboard
    """
    roulette = Roulette()

    keyboards.build_exclude_keyboard(update, context, roulette.participants)
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


def process(update: Update, context: CallbackContext):
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


def update_wishes_list(update: Update, context: CallbackContext):
    """Met à jour la liste des cadeaux."""
    if santa.get_cadeaux():
        text = "liste des cadeaux inchangée\n"
    else:
        text = "liste des cadeaux mise à jour\n"

    context.bot.send_message(chat_id=update.message.chat_id, text=text)
    logger.info(text)
