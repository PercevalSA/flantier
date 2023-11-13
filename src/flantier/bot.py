#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

import logging

from telegram import (
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Dispatcher,
    Filters,
    MessageHandler,
    Updater,
)

from flantier import _keyboards
from flantier._commands_admin import (
    add_spouse,
    close_registrations,
    open_registrations,
    process,
    update_wishes_list,
)
from flantier._commands_flantier import hello, quote_oss1, quote_oss2
from flantier._commands_gift import comments, dont_offer, offer, wishes
from flantier._commands_user import get_result, list_users, register, unregister
from flantier._settings import SettingsManager
from flantier._users import UserManager

# Enable logging, we do not need "%(asctime)s - %(name)s as it is already printed by ptb
logging.basicConfig(format="%(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("flantier")


def start(update: Update, context: CallbackContext) -> None:
    """Start the interaction with the bot. Enable the bot to talk to user."""
    context.bot.send_message(
        chat_id=update.effective_chat.id,  # type: ignore
        text=(
            "🧑‍🎄 C'est bientôt Noël! "
            "Je suis là pour vous aider à organiser tout ça Larmina mon p'tit. "
            "Je tire au sort les cadeaux et vous nous faites une jolie table "
            "avec une bonne bûche pour le dessert 🪵"
        ),
    )
    logger.info(
        "Received a start command from user %s: %d in chat %s: %d",
        update.message.from_user.username,
        update.message.from_user.id,
        update.effective_chat.full_name,  # type: ignore
        update.message.chat_id,
    )

    UserManager().add_user(
        tg_id=update.message.from_user.id,
        name=update.effective_chat.full_name.split(" ")[0],
    )


def help_message(update: Update, context: CallbackContext) -> None:
    """Send the help message with all available commands"""
    simple_help = """Voici les commandes disponibles:
/aide - affiche cette aide
/participer - s'inscrire pour le secret santa
/retirer - se désinscrire du secret santa
/liste - donne la liste des participants
/resultat - donne le résultat tu tirage au sort en dm

/bonjour - je vous dirai bonjour à ma manière
/larmina - le caire nid d'espion
/dolores - rio ne répond plus

Les commandes aussi sont disponibles en anglais:
/help, /hello, /register, /remove, /list, /result
"""

    extended_help = """

/cadeaux - donne la liste des voeux de cadeaux
/commentaires - donne les commentaires associés aux voeux
/offrir - reserve un cadeau à offrir (pour que personne d'autre ne l'offre)
/retirer - annule la réservation
/annuler - annule l'opération en cours
    """

    admin_help = """

Commandes administrateur:
/start - démarre l'interaction avec le bot
/open - ouvre la session d'inscription
/close - termine la session d'inscription
/tirage - lance le tirage au sort avec les contraintes
/exclude - ajoute une contrainte de destinataire (conjoint)
"""

    if SettingsManager().settings["flantier"]["extended_mode"]:
        help_text = simple_help + extended_help + admin_help
    else:
        help_text = simple_help + admin_help

    context.bot.send_message(
        chat_id=update.effective_chat.id,  # type: ignore
        text=help_text,
    )


def cancel(update: Update, context: CallbackContext) -> None:
    """Cancel current operation and reset flantier state."""
    reply_del_kb = ReplyKeyboardRemove()
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Opération annulée.",
        reply_markup=reply_del_kb,
    )


def unknown_command(update: Update, context: CallbackContext) -> None:
    """Gère les commandes inconues ou incorrectes"""
    context.bot.send_message(
        chat_id=update.effective_chat.id,  # type: ignore
        text="Le Mue... quoi? Je n'ai pas compris cette commande.",
    )


def register_commands(dispatcher: Dispatcher, extended_mode: bool = False) -> None:
    """Register all commands."""

    # generic bot commands
    dispatcher.add_handler(CommandHandler("start", start))

    # users commands
    dispatcher.add_handler(CommandHandler("bonjour", hello))
    dispatcher.add_handler(CommandHandler("hello", hello))
    dispatcher.add_handler(CommandHandler("larmina", quote_oss1))
    dispatcher.add_handler(CommandHandler("dolores", quote_oss2))
    dispatcher.add_handler(CommandHandler("participer", register))
    dispatcher.add_handler(CommandHandler("register", register))
    dispatcher.add_handler(CommandHandler("retirer", unregister))
    dispatcher.add_handler(CommandHandler("remove", unregister))
    dispatcher.add_handler(CommandHandler("liste", list_users))
    dispatcher.add_handler(CommandHandler("list", list_users))
    dispatcher.add_handler(CommandHandler("resultat", get_result))
    dispatcher.add_handler(CommandHandler("result", get_result))
    dispatcher.add_handler(CommandHandler("aide", help_message))
    dispatcher.add_handler(CommandHandler("help", help_message))

    if extended_mode:
        dispatcher.add_handler(CommandHandler("cadeaux", wishes))
        dispatcher.add_handler(CommandHandler("commentaires", comments))
        dispatcher.add_handler(CommandHandler("offrir", offer))
        dispatcher.add_handler(CommandHandler("retirer", dont_offer))
        dispatcher.add_handler(CommandHandler("annuler", cancel))

    # admin commands
    dispatcher.add_handler(CommandHandler("open", open_registrations))
    dispatcher.add_handler(CommandHandler("close", close_registrations))
    dispatcher.add_handler(CommandHandler("tirage", process))
    dispatcher.add_handler(CommandHandler("exclude", add_spouse))

    if extended_mode:
        dispatcher.add_handler(CommandHandler("update", update_wishes_list))

    # inline kb
    dispatcher.add_handler(CommandHandler("contraintes", _keyboards.inline_kb))
    dispatcher.add_handler(CallbackQueryHandler(_keyboards.button))

    # unkown commands
    dispatcher.add_handler(MessageHandler(Filters.command, unknown_command))


def error(update: Update, context: CallbackContext) -> None:
    """Bot error handler."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main() -> None:
    """Start the bot."""
    settings = SettingsManager().load_settings()
    logger.info(settings)
    # Create the EventHandler and pass it your bot's token
    updater = Updater(token=settings["telegram"]["bot_token"])

    # answer in Telegram on different commands
    register_commands(updater.dispatcher, settings["flantier"]["extended_mode"])

    # log all errors
    updater.dispatcher.add_error_handler(error)

    # init users
    UserManager().load_users()

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
