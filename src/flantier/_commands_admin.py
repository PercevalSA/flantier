"""Admin Commands"""

from logging import getLogger

from telegram import (
    Bot,
    ForceReply,
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

    # send results to everyone as private message
    user_manager = UserManager()
    for user in user_manager.users:
        if not user.registered:
            pass

        giftee = user_manager.get_user(user.giftee)
        logger.info("send result to %s: giftee is %d", user.name, giftee.tg_id)

        context.bot.send_message(
            user.tg_id,
            text=f"🎅 Youpi tu offres à {giftee.name}\n",
        )


# LEGACY
#########


def add_spouse(update: Update, context: CallbackContext) -> None:
    """Ajoute un conjoint à un participant.
    provide names supplier and forbidden recipient else display people keyboard
    """
    if not is_admin(update, context):
        return

    user_manager = UserManager()

    assert context.args

    for name in context.args:
        user = user_manager.search_user(name)
        logger.info("searching for %s", name)

        if not user or user.tg_id == update.message.from_user.id:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text=f"❌ Je n'ai pas trouvé {name} dans la liste des inscrits. 😕",
            )
            logger.info("cannot find user: %s", name)
            return

    if len(context.args) == 1:  # type: ignore
        force_reply = ForceReply(
            force_reply=True,
            selective=False,
        )

        # type: ignore
        reply_keyboard = _keyboards.build_people_keyboard("/exclude " + context.args[0])

        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="🙅 Qui ne doit pas recevoir de qui? 🙅",
            reply_to_message_id=update.message.message_id,
            reply_markup=force_reply,
        )
        context.bot.send_message(
            chat_id=update.message.chat_id,
            # type: ignore
            text=f"Selectionne le ou la conjoint.e de {context.args[0]}",
            reply_markup=reply_keyboard,
        )
        return

    if len(context.args) != 2:  # type: ignore
        force_reply = ForceReply(
            force_reply=True,
            selective=False,
        )

        reply_keyboard = _keyboards.build_people_keyboard("/exclude")

        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="🙅 Qui ne doit pas offrir à qui? 🙅",
            reply_to_message_id=update.message.message_id,
            reply_markup=force_reply,
        )
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Selectionne la personne qui n'a pas le droit d'offrir à quelqu'un",
            reply_markup=reply_keyboard,
        )
        return

    # get the tg_id of the user which the name has been given in message[1]
    # and add it as spouse
    giver = user_manager.search_user(context.args[0])  # type: ignore
    spouse = user_manager.search_user(context.args[1])  # type: ignore
    if spouse.tg_id == giver.tg_id:
        context.bot.send_message(chat_id=update.message.chat_id, text="❌ impossibru")
        logger.info(
            "giver (%s) and spouse (%s) are the same person.", giver.name, spouse.name
        )
        return

    user_manager.set_spouse(update.message.from_user.id, spouse.tg_id)
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=(
            "📝 c'est bien noté! 📝\n"
            f"🧑‍🤝‍🧑 {context.args[1]} est le/la conjoint.e "  # type: ignore
            f"de {context.args[0]}"  # type: ignore
        ),
    )
    logger.info("set spouse %s for %s", context.args[0], context.args[1])  # type: ignore


def register_admin_commands(dispatcher: Dispatcher) -> None:
    """Register all admin commands."""
    dispatcher.add_handler(CommandHandler("open", open_registrations))
    dispatcher.add_handler(CommandHandler("close", close_registrations))
    dispatcher.add_handler(CommandHandler("tirage", process))
    dispatcher.add_handler(CommandHandler("exclude", add_spouse))
