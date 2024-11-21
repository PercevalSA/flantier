"""User commands"""

from logging import getLogger

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
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


async def self_register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Permet de s'inscrire au tirage au sort."""
    logger.debug("register: %s", update.message.from_user)
    text = _register_user(
        update.message.from_user.id, update.message.from_user.first_name
    )
    await context.bot.send_message(chat_id=update.message.chat_id, text=text)


async def self_unregister(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    await context.bot.send_message(chat_id=update.message.chat_id, text=text)


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Liste les participants inscrits."""
    users_list = "\n".join(u.name for u in UserManager().users if u.registered)
    if users_list:
        text = f"🙋 Les participant.e.s sont:\n{users_list}"
    else:
        text = "😢 Aucun.e participant.e n'est encore inscrit.e."

    await context.bot.send_message(chat_id=update.message.chat_id, text=text)


async def get_constraints(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with user constraints as inline buttons attached."""
    user_manager = UserManager()
    text = "<b>Contraintes</b>\n"
    for user in user_manager.users:
        if user.registered:
            text += user_manager.get_user_constraints(user.tg_id) + "\n"

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def get_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Affiche le résultat du tirage au sort en message privé."""
    user_manager = UserManager()
    supplier = user_manager.get_user(update.message.from_user.id)
    receiver = user_manager.get_user(supplier.giftee)

    if receiver is None:
        text = "🤷 Il y'a eu une erreur, tu n'offres à personne pour l'instant"
    else:
        text = f"🎅 Youpi tu offres à : {receiver.name} 🎁\n"

    await context.bot.send_message(chat_id=update.message.from_user.id, text=text)


def register_user_commands(application: Application) -> None:
    """Register user commands to the application."""
    application.add_handler(CommandHandler("participer", self_register))
    application.add_handler(CommandHandler("retirer", self_unregister))
    application.add_handler(CommandHandler("liste", list_users))
    application.add_handler(CommandHandler("resultat", get_result))
    application.add_handler(CommandHandler("contraintes", get_constraints))
