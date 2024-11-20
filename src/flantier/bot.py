"""Herr Flantier der Geschenk Manager."""

import logging
from threading import Thread

from telegram import ParseMode, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Dispatcher,
    Filters,
    MessageHandler,
    Updater,
)

from flantier._commands_admin import register_admin_commands
from flantier._commands_flantier import register_flantier_commands
from flantier._commands_santa import register_santa_commands
from flantier._commands_user import register_user_commands
from flantier._keyboards import register_keyboards
from flantier._santa import update_gifts_background_task
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
        name=update.message.from_user.first_name,
    )


def help_message(update: Update, context: CallbackContext) -> None:
    """Send the help message with all available commands"""
    help_text = """
<b>🤵‍♂️ Commandes Utilisateur.ice.s</b>
/start - démarre l'interaction avec le bot
/aide - affiche cette aide

<b>🎡 Tirage au sort</b>
/participer - s'inscrire pour le secret santa
/retirer - se désinscrire du secret santa
/liste - affiche la liste des participants
/contraintes - affiche les contraintes du tirage au sort (conjoint et tirage de l'an dernier)
/resultat - envoie le résultat tu tirage au sort en message privé

<b>🎁 Cadeaux</b>
/cadeaux - donne la liste des voeux de cadeaux d'un.e participant.e
/commentaires - donne les commentaires associés aux voeux
/offrir - reserve un cadeau à offrir (pour que personne d'autre ne l'offre) [🅱️ETA]
/reprendre - annule la réservation du cadeau [☕️TODO] (donner c'est donner, reprendre c'est voler - comme la propriété privée)
/update - met à jour la liste des souhaits depuis google sheets

<b>🕵️ OSS 117</b>
/bonjour - je vous dirai bonjour à ma manière
/larmina - le caire nid d'espion
/dolores - rio ne répond plus

<b>👮‍♀️ Commandes administrateur.ice</b>
/open - ouvre la session d'inscription
/close - termine la session d'inscription
/register - inscrit un.e participant.e
/unregister - désinscrit un.e participant.e
/spouse - ajoute une contrainte de destinataire (conjoint.e)
/tirage - lance le tirage au sort avec les contraintes
💡 La liste des souhaits est mise à jour automatiquement toutes les 10 minutes.
"""

    context.bot.send_message(
        chat_id=update.effective_chat.id,  # type: ignore
        text=help_text,
        parse_mode=ParseMode.HTML,
    )


def unimplemented_command(update: Update, context: CallbackContext) -> None:
    """Send the help message with all available commands"""
    help_text = (
        "Désolé larmina mon p'tit mais cette commande n'est pas encore implémentée."
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,  # type: ignore
        text=help_text,
    )


def unknown_command(update: Update, context: CallbackContext) -> None:
    """Gère les commandes inconues ou incorrectes"""
    context.bot.send_message(
        chat_id=update.effective_chat.id,  # type: ignore
        text="Le Mue... quoi? Je n'ai pas compris cette commande.",
    )


def register_commands(dispatcher: Dispatcher) -> None:
    """Register all commands."""

    # generic bot commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("aide", help_message))
    dispatcher.add_handler(CommandHandler("help", help_message))

    register_keyboards(dispatcher)
    register_user_commands(dispatcher)
    register_santa_commands(dispatcher)
    register_flantier_commands(dispatcher)
    register_admin_commands(dispatcher)

    dispatcher.add_handler(CommandHandler("retirer", unimplemented_command))

    # handle all unkown commands
    dispatcher.add_handler(MessageHandler(Filters.command, unknown_command))


def error(update: Update, context: CallbackContext) -> None:
    """Bot error handler."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main() -> None:
    """Start the bot."""
    settings = SettingsManager().load_settings()
    logger.debug("Settings: %s", settings)
    # Create the EventHandler and pass it your bot's token
    updater = Updater(token=settings["telegram"]["bot_token"])

    # answer in Telegram on different commands
    register_commands(updater.dispatcher)  # type: ignore

    # log all errors
    updater.dispatcher.add_error_handler(error)  # type: ignore

    # init users
    UserManager().load_users()

    # update gifts in database every 10 minutes
    thread = Thread(target=update_gifts_background_task)
    thread.start()

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

    thread.join()
