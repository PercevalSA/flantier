#!/usr/bin/python3
"""User commands."""

from logging import getLogger

from telegram import (
    Update,
)
from telegram.ext import (
    CallbackContext,
)

from flantier._roulette import Roulette
from flantier._users import UserManager

logger = getLogger("flantier")


def _register_user(user_id: int, user_name: str) -> str:
    roulette = Roulette()
    user_manager = UserManager()
    logger.info("user %s requested registration: %d", user_name, user_id)

    # users are created with the start command, if not we should create them
    if not user_manager.get_user(user_id):
        user_manager.add_user(tg_id=user_id, name=user_name)

    if not roulette.registration:
        return (
            f"🦋 Patience {user_name},\n"
            "🙅 les inscriptions n'ont pas encore commencées ou sont déjà terminées!"
        )

    if user_manager.get_user(user_id).registered:  # type: ignore
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
    if Roulette().unregister_user(update.message.from_user.id):
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
    users_list = UserManager().users
    if users_list:
        text = f"🙋 Les participant.e.s sont:\n{users_list}"
    else:
        text = "😢 Aucun.e participant.e n'est encore inscrit.e."

    context.bot.send_message(chat_id=update.message.chat_id, text=text)

    # FIXME find another way to check that we have access to all users private chats
    for user in UserManager().users:
        logger.info("Envoi du message privé à %s", user.name)
        context.bot.send_message(user.tg_id, text="🧪 Test de message privé 🧪")


def get_result(update: Update, context: CallbackContext) -> None:
    """Affiche le résultat du tirage au sort en message privé."""
    user_manager = UserManager()
    supplier = user_manager.get_user(update.message.from_user.id)
    receiver = user_manager.get_user(supplier.giftee)

    context.bot.send_message(
        chat_id=update.message.from_user.id,
        text=f"🎅 Youpi tu offres à : {receiver.name} 🎁\n",
    )
