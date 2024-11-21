"""Admin Commands"""

from logging import getLogger

from telegram import (
    Bot,
    Update,
)
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from flantier._roulette import Roulette
from flantier._settings import SettingsManager
from flantier._users import UserManager

logger = getLogger("flantier")


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
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
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="🙅 Petit.e canaillou! Tu ne possèdes pas ce pouvoir.",
        )
        return False

    return True


async def send_admin_notification(message: str) -> None:
    """send a telegram message to the bot administrator

    Args:
        message (str): message content to send
    """
    settings = SettingsManager().settings
    await Bot(token=settings["telegram"]["bot_token"]).send_message(
        chat_id=settings["telegram"]["administrator"],
        text=(
            "Changer le monde, changer le monde vous êtes bien sympathiques mais faudrait"
            " déjà vous levez le matin.\n\n" + message
        ),
    )


async def update_last_year_giftees(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Update the last year giftees for all users to use them as constraints for this year
    Takes the giftee of each user and put it in last_giftee field and reset giftee field.
    """
    if not is_admin(update, context):
        return
    logger.info("updating last year giftees for all users")
    UserManager().update_with_last_year_results()
    await update.message.reply_text(
        "🎅 Les résultats de l'année dernière ont été utilisés "
        "en tant que contraintes pour cette année."
    )


async def open_registrations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lance la campagne d'inscription. Récupère les résultats de l'année précédente
    comme nouvelles conditions de tirage au sort.
    """
    if not is_admin(update, context):
        return

    Roulette().open_registrations()

    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=(
            "🎉 Les inscriptions sont ouvertes\n"
            "🎅 Vous pouvez désormais vous inscrire en envoyant /participer"
        ),
    )


async def close_registrations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Termine la campagne d'inscription."""
    if not is_admin(update, context):
        return

    Roulette().close_registrations()

    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=("🙅 Les inscriptions sont fermées\n⏰ C'est bientôt l'heure des résultats"),
    )


async def draw_secret_santas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lance le tirage au sort et envoie les réponses en message privé."""
    if not is_admin(update, context):
        return

    roulette = Roulette()

    if not roulette.is_ready():
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="⚠️ Les inscriptions ne sont pas encore terminées.",
        )
        return

    message = await context.bot.send_message(
        chat_id=update.message.chat_id, text="🎡 Tirage au sort en cours..."
    )
    if roulette.tirage() != 0:
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="⚠️ Le tirage au sort n'a pas pu être effectué.",
        )
        return

    await context.bot.edit_message_text(
        message_id=message.message_id,
        chat_id=message.chat.id,
        text="🎡 Tirage au sort terminé ✅",
    )


async def send_result_to_all_users(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """send results to everyone as private message"""
    if not is_admin(update, context):
        return

    user_manager = UserManager()
    for user in user_manager.users:
        if not user.registered or user.tg_id <= 0:
            logger.debug("skip user %s: %d", user.name, user.tg_id)
            continue

        giftee = user_manager.get_user(user.giftee)
        if giftee is None:
            logger.error("giftee not found for %s: %d", user.name, user.giftee)
            continue

        logger.info("send result to %s: giftee is %d", user.name, giftee.tg_id)

        try:
            await context.bot.send_message(
                user.tg_id,
                text=f"🎅 Youpi tu offres à {giftee.name}",
            )
        except TelegramError as e:
            logger.error("error sending message to %s: %s", user.name, e)

        await context.bot.send_message(
            update.message.chat_id,
            text="🦹‍♂️ tous les parents Noël secrets ont été envoyés aux interessé.e.s",
        )


def register_admin_commands(application: ApplicationBuilder) -> None:
    """Register all admin commands. Manage the secret santa regisrations and draw"""
    application.add_handler(CommandHandler("open", open_registrations))
    application.add_handler(CommandHandler("close", close_registrations))
    application.add_handler(CommandHandler("tirage", draw_secret_santas))
    application.add_handler(CommandHandler("results", send_result_to_all_users))
    application.add_handler(CommandHandler("newyear", update_last_year_giftees))
