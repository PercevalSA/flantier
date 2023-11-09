#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

import logging

from roulette import Roulette
from telegram import (
    Update,
)
from telegram.ext import (
    CallbackContext,
)

logger = logging.getLogger("flantier")

#########################
# COMMANDES UTILISATEUR #
#########################


def register(update: Update, context: CallbackContext):
    """Permet de s'inscrire au tirage au sort."""
    roulette = Roulette()
    not_registered = roulette.add_user(
        tg_id=update.message.from_user.id, name=update.message.from_user.first_name
    )
    if not not_registered:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=(
                f"🎉 Bravo {update.message.from_user.first_name} 🎉\n"
                "Tu es bien enregistré.e pour le tirage au sort"
            ),
        )

    elif not_registered == -1:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=(
                f"🦋 Patience {update.message.from_user.first_name},\n"
                "🙅 les inscriptions n'ont pas encore commencées ou sont déj"
                "à terminées!"
            ),
        )

    elif not_registered == -2:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=(
                f"{update.message.from_user.first_name}, petit coquinou! Tu t'es déjà"
                " inscrit.e. Si tu veux recevoir un deuxième cadeau, tu peux te faire"
                " un auto-cadeau 🤷🔄🎁"
            ),
        )


def unregister(update: Update, context: CallbackContext):
    """Permet de se désinscrire du tirage au sort."""
    roulette = Roulette()

    if roulette.remove_user(update.message.from_user.id):
        text = (
            f"🗑 {update.message.from_user.first_name} "
            "a bien été retiré.e du tirage au sort."
        )
    else:
        text = (
            f"🤷 {update.message.from_user.first_name} "
            "n'a jamais été inscrit.e au tirage au sort..."
        )

    context.bot.send_message(chat_id=update.message.chat_id, text=text)


def list_users(update: Update, context: CallbackContext):
    """Liste les participants inscrits."""
    roulette = Roulette()
    users = roulette.list_users()

    if len(users):
        text = f"🙋 Les participant.e.s sont:\n{users}"
    else:
        text = "😢 Aucun.e participant.e n'est encore inscrit.e."

    context.bot.send_message(chat_id=update.message.chat_id, text=text)

    # on check qu'on a accès aux chats privés de tous les participants
    for user in roulette.participants:
        logger.info("Envoi du message privé à %s", user["name"])
        context.bot.send_message(
            user["tg_id"],
            text="🧪 Test",
        )


def get_result(update: Update, context: CallbackContext):
    """Affiche le résultat du tirage au sort en message privé."""
    roulette = Roulette()
    supplier = roulette.get_user(update.message.from_user.id)
    receiver = roulette.get_user(supplier["giftee"])

    context.bot.send_message(
        chat_id=update.message.from_user.id,
        text=f"🎅 Youpi tu offres à : {receiver['name']} 🎁\n",
    )