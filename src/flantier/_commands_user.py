#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

import logging

from telegram import (
    Update,
)
from telegram.ext import (
    CallbackContext,
)

from flantier._roulette import Roulette

logger = logging.getLogger("flantier")

#########################
# COMMANDES UTILISATEUR #
#########################


def _register_user(user_id: int, user_name: str) -> str:
    roulette = Roulette()
    logger.info("user %s requested registration: %d", user_name, user_id)

    # users are created with the start command, if not we should create them
    if not roulette.get_user(user_id):
        roulette.add_user(tg_id=user_id, name=user_name)

    if not roulette.registration:
        return (
            f"🦋 Patience {user_name},\n"
            "🙅 les inscriptions n'ont pas encore commencées ou sont déjà terminées!"
        )

    if roulette.get_user(user_id).registered:
        return (
            f"{user_name}, petit coquinou! Tu t'es déjà inscrit.e. "
            "Si tu veux recevoir un deuxième cadeau, "
            "tu peux te faire un auto-cadeau 🤷🔄🎁"
        )

    if roulette.register_user(tg_id=user_id, name=user_name):
        return f"🎉 Bravo {user_name} 🎉\nTu es bien enregistré.e pour le tirage au sort"

    return f"❌ désolé {user_name}, il y'a eu un problème lors de ton inscription 😢"


def register(update: Update, context: CallbackContext) -> None:
    """Permet de s'inscrire au tirage au sort."""
    logger.info("register: %s", update.message.from_user)
    text = _register_user(
        update.message.from_user.id, update.message.from_user.first_name
    )
    context.bot.send_message(chat_id=update.message.chat_id, text=text)


def unregister(update: Update, context: CallbackContext) -> None:
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


def list_users(update: Update, context: CallbackContext) -> None:
    """Liste les participants inscrits."""
    roulette = Roulette()
    users = roulette.list_users()

    if users:
        text = f"🙋 Les participant.e.s sont:\n{users}"
    else:
        text = "😢 Aucun.e participant.e n'est encore inscrit.e."

    context.bot.send_message(chat_id=update.message.chat_id, text=text)

    # on check qu'on a accès aux chats privés de tous les participants
    for user in roulette.participants:
        logger.info("Envoi du message privé à %s", user.name)
        context.bot.send_message(
            user.tg_id,
            text="🧪 Test",
        )


def get_result(update: Update, context: CallbackContext) -> None:
    """Affiche le résultat du tirage au sort en message privé."""
    roulette = Roulette()
    supplier = roulette.get_user(update.message.from_user.id)
    receiver = roulette.get_user(supplier["giftee"])

    context.bot.send_message(
        chat_id=update.message.from_user.id,
        text=f"🎅 Youpi tu offres à : {receiver['name']} 🎁\n",
    )
