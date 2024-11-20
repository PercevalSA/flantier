"""Admin Commands"""

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

from flantier._roulette import Roulette
from flantier._settings import SettingsManager
from flantier._users import UserManager

logger = getLogger("flantier")


def is_admin(update: Update, context: CallbackContext) -> bool:
    """check if the given telegram id is admin of the bot

    Returns:
        bool: whether the telegram user is admin of the bot or not
    """

    logger.info(
        "%s requested admin rights: %d",
        update.message.from_user.username,
        update.message.from_user.id,
    )

    if (
        update.message.from_user.id
        != SettingsManager().settings["telegram"]["administrator"]
    ):
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="🙅 Petit.e canaillou! Tu ne possèdes pas ce pouvoir.",
        )
        return False

    return True


def send_admin_notification(message: str) -> None:
    """send a telegram message to the bot administrator

    Args:
        message (str): message content to send
    """
    administrator = SettingsManager().settings["telegram"]["administrator"]
    Bot(token=SettingsManager().settings["telegram"]["bot_token"]).send_message(
        chat_id=administrator,
        text=(
            "Changer le monde, changer le monde vous êtes bien sympathiques mais faudrait"
            " déjà vous levez le matin.\n\n" + message
        ),
    )


def open_registrations(update: Update, context: CallbackContext) -> None:
    """Lance la campagne d'inscription. Récupère les résultats de l'année précédente
    comme nouvelles conditions de tirage au sort.
    """
    if not is_admin(update, context):
        return

    Roulette().open_registrations()
    UserManager().update_with_last_year_results()

    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=(
            "🎉 Les inscriptions sont ouvertes\n"
            "🎅 Vous pouvez désormais vous inscrire en envoyant /participer"
        ),
    )


def close_registrations(update: Update, context: CallbackContext) -> None:
    """Termine la campagne d'inscription."""
    if not is_admin(update, context):
        return

    Roulette().close_registrations()

    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=("🙅 Les inscriptions sont fermées\n⏰ C'est bientôt l'heure des résultats"),
    )


def process(update: Update, context: CallbackContext) -> None:
    """Lance le tirage au sort et envoie les réponses en message privé."""
    if not is_admin(update, context):
        return

    roulette = Roulette()
    message = context.bot.send_message(
        chat_id=update.message.chat_id, text="🎡 Tirage au sort en cours..."
    )

    if not roulette.is_ready():
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="⚠️ Les inscriptions ne sont pas encore terminées.",
        )
        return

    if roulette.tirage() != 0:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="⚠️ Le tirage au sort n'a pas pu être effectué.",
        )
        return

    context.bot.edit_message_text(
        message_id=message.message_id,
        chat_id=message.chat.id,
        text="🎡 Tirage au sort terminé ✅",
    )
    # send results to everyone as private message
    user_manager = UserManager()
    for user in user_manager.users:
        if not user.registered or user.tg_id <= 0:
            logger.debug("skip user %s: %d", user.name, user.tg_id)
            continue

        giftee = user_manager.get_user(user.giftee)
        logger.info("send result to %s: giftee is %d", user.name, giftee.tg_id)

        context.bot.send_message(
            user.tg_id,
            text=f"🎅 Youpi tu offres à {giftee.name}\n",
        )


def register_admin_commands(dispatcher: Dispatcher) -> None:
    """Register all admin commands."""
    dispatcher.add_handler(CommandHandler("open", open_registrations))
    dispatcher.add_handler(CommandHandler("close", close_registrations))
    dispatcher.add_handler(CommandHandler("tirage", process))
    dispatcher.add_handler(CommandHandler("exclude", add_spouse))
