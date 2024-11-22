"""Herr Flantier der Geschenk Manager."""

from logging import getLogger

from telegram import (
    Bot,
    Update,
)
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Dispatcher,
)

from flantier import _santa
from flantier._keyboards import build_people_inline_kb
from flantier._settings import SettingsManager
from flantier._users import Wish

logger = getLogger("flantier")


def get_wishes(update: Update, _: CallbackContext) -> None:
    """Send a message with user list as inline buttons attached.
    Clicking a button returns the user's wish list.
    """
    keyboard = build_people_inline_kb("wishes")
    update.message.reply_text(
        "🤷 De qui veux tu consulter la liste de souhaits?", reply_markup=keyboard
    )


def get_wishes_and_comments(update: Update, _: CallbackContext) -> None:
    """Affiche la liste de cadeaux et les commentaires associés d'une personne."""
    keyboard = build_people_inline_kb("comments")
    update.message.reply_text(
        "🤷 De qui veux tu consulter la liste de souhaits?", reply_markup=keyboard
    )


def update_wishes_list(update: Update, context: CallbackContext) -> None:
    """Met à jour la liste des cadeaux dans le cache du bot depuis le google sheet."""
    _santa.create_missing_users()
    _santa.update_wishes_list()
    text = "🎁 liste des cadeaux mise à jour."
    context.bot.send_message(chat_id=update.message.chat_id, text=text)


def send_giver_notification(wish: Wish) -> None:
    """send a notification to the giver of a wish that has been changed or updated
    in database in order to confirm that it didn't changed completely
    and that the giver still want to give this gift
    """
    if wish.giver:
        Bot(token=SettingsManager().settings["telegram"]["bot_token"]).send_message(
            chat_id=wish.giver,
            text=(
                "🔄 Le cadeau que tu avais prévu d'offrir a changé: {wish.wish}.\nVeux-tu"
                " toujours l'offir? Si non utilises la commande /offrir"
            ),
        )


def register_santa_commands(dispatcher: Dispatcher) -> None:
    """Register all the santa commands: specific to gifts and wishess management"""
    dispatcher.add_handler(CommandHandler("cadeaux", get_wishes))
    dispatcher.add_handler(CommandHandler("commentaires", get_wishes_and_comments))
    dispatcher.add_handler(CommandHandler("update", update_wishes_list))
