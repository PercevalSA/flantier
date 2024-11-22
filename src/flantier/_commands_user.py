"""User commands"""

from logging import getLogger

from telegram import ParseMode, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Dispatcher,
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

    if roulette.register_user(tg_id=user_id):
        return f"🎉 Bravo {user_name} 🎉\nTu es bien enregistré.e pour le tirage au sort"

    logger.error("registration failed for user %s: %d", user_name, user_id)
    return f"❌ désolé {user_name}, il y'a eu un problème lors de ton inscription 😢"


def self_register(update: Update, context: CallbackContext) -> None:
    """Permet de s'inscrire au tirage au sort."""
    logger.debug("register: %s", update.message.from_user)
    text = _register_user(
        update.message.from_user.id, update.message.from_user.first_name
    )
    context.bot.send_message(chat_id=update.message.chat_id, text=text)


def self_unregister(update: Update, context: CallbackContext) -> None:
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
    users_list = "\n".join(u.name for u in UserManager().users if u.registered)
    if users_list:
        text = f"🙋 Les participant.e.s sont:\n{users_list}"
    else:
        text = "😢 Aucun.e participant.e n'est encore inscrit.e."

    context.bot.send_message(chat_id=update.message.chat_id, text=text)


def get_constraints(update: Update, _: CallbackContext) -> None:
    """Send a message with user constraints as inline buttons attached."""
    user_manager = UserManager()
    text = "<b>Contraintes</b>\n"
    for user in user_manager.users:
        if user.registered:
            text += user_manager.get_user_constraints(user.tg_id) + "\n"

    update.message.reply_text(text, parse_mode=ParseMode.HTML)


def get_result(update: Update, context: CallbackContext) -> None:
    """Affiche le résultat du tirage au sort en message privé."""
    user_manager = UserManager()
    supplier = user_manager.get_user(update.message.from_user.id)
    receiver = user_manager.get_user(supplier.giftee)

    if receiver is None:
        text = "🤷 Il y'a eu une erreur, tu n'offres à personne pour l'instant"
    else:
        text = f"🎅 Youpi tu offres à : {receiver.name} 🎁\n"

    context.bot.send_message(chat_id=update.message.from_user.id, text=text)


def register_user_commands(dispatcher: Dispatcher) -> None:
    """Register user commands to the dispatcher."""
    dispatcher.add_handler(CommandHandler("participer", self_register))
    dispatcher.add_handler(CommandHandler("retirer", self_unregister))
    dispatcher.add_handler(CommandHandler("liste", list_users))
    dispatcher.add_handler(CommandHandler("resultat", get_result))
    dispatcher.add_handler(CommandHandler("contraintes", get_constraints))
