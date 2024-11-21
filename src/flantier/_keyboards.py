"""gestion des claviers interractifs dans telegram"""

from logging import getLogger
from typing import Any

from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from flantier._commands_admin import is_admin
from flantier._roulette import Roulette
from flantier._santa import (
    set_wish_giver,
    user_comments_message,
    user_wishes_message,
)
from flantier._users import UserManager

logger = getLogger("flantier")

COLUMNS = 2


def build_people_inline_kb(
    command: str,
    extra_data: Any = None,
    filter_registered: bool = False,
) -> InlineKeyboardMarkup:
    """build an inline keyboard based on user names.
    Créer le clavier avec les noms des participants. Ajoute la commande en prefix
    /offrir, /cadeaux, /commentaires, /exclude

    call back data allow to identify the command the user wants to execute
    we set in callback the command and the user id (and name) to execute the command on
    filter_registered is used as logic implication which is equivalent to (not A or B)
    https://fr.wikipedia.org/wiki/Table_de_v%C3%A9rit%C3%A9#Implication_logique
    """
    tkeyboard = [
        InlineKeyboardButton(
            user.name,
            callback_data=f"user {command} { str(user.tg_id)}"
            + (f" {str(extra_data)}" if extra_data is not None else ""),
        )
        for user in UserManager().users
        if (not filter_registered or user.registered)
    ]
    tkeyboard.append(InlineKeyboardButton("Annuler", callback_data="cancel 0 cancel"))
    # split keyboard in two columns
    keyboard = [tkeyboard[i : i + COLUMNS] for i in range(0, len(tkeyboard), COLUMNS)]
    return InlineKeyboardMarkup(keyboard)


async def spouse_inline_kb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with user spouse as inline buttons attached."""
    if not is_admin(update, context):
        await update.message.reply_text("🙅 Tu n'as pas les droits pour cette commande.")
        return

    keyboard = build_people_inline_kb("spouse", filter_registered=True)
    logger.info("spouse keyboard built")
    await update.message.reply_text(
        "👬 De qui veux tu configurer le ou la partenaire?", reply_markup=keyboard
    )


async def giftee_inline_kb(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with user wishes as inline buttons attached."""
    keyboard = build_people_inline_kb("offer")
    logger.info("giftee keyboard built")
    await update.message.reply_text("🎁 À qui veux-tu offrir ?", reply_markup=keyboard)


async def register_inline_kb(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with user names as inline buttons attached."""
    keyboard = build_people_inline_kb("register")
    logger.info("register keyboard built")
    await update.message.reply_text("✍️ Qui veux-tu inscrire ?", reply_markup=keyboard)


async def unregister_inline_kb(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with user names as inline buttons attached."""
    keyboard = build_people_inline_kb("unregister", filter_registered=True)
    logger.info("unregister keyboard built")
    await update.message.reply_text("✍️ Qui veux-tu désinscrire ?", reply_markup=keyboard)


async def user_button(query: CallbackQuery) -> None:
    """Parses the CallbackQuery and updates the message text from people inline keyboard.
    data is like "user <command> <user_id> <user_name>
    """
    data = await query.data.split(" ")
    logger.info("keyboard query data: %s", data)
    command = data[1]
    user_id = int(data[2])

    text = ""
    markup = None
    user_manager = UserManager()
    user_name = user_manager.get_user(user_id).name

    if command == "register":
        if Roulette().register_user(user_id):
            text = f"🎡 {user_name} est bien enregistré.e pour le tirage au sort."
        else:
            text = (
                f"❌ impossible d'inscrire {user_name} au tirage au sort. "
                "Vérifiez que les inscriptions sont ouvertes."
            )

    if command == "unregister":
        if Roulette().unregister_user(user_id):
            text = f"🗑 {user_name} a bien été retiré.e du tirage au sort."
        else:
            text = f"🤷 {user_name} n'a jamais été inscrit.e au tirage au sort..."

    if command == "wishes":
        text = user_wishes_message(user_name)

    if command == "comments":
        text = user_comments_message(user_name)

    if command == "offer":
        text = "🎁 Que veux tu offrir comme cadeau ?"
        markup = build_wishes_inline_kb(user_name)

    if command == "spouse":
        text = (
            f"💁 Qui est le ou la partenaire de {user_name}? "
            "Iel ne pourra pas lui offrir."
        )
        markup = build_people_inline_kb(
            "exclude", extra_data=user_id, filter_registered=True
        )

    if command == "exclude":
        spouse_user_id = int(data[3])
        spouse_name = user_manager.get_user(spouse_user_id).name
        text = (
            f"👭 {user_name} et {spouse_name} sont partenaires. "
            "Iels ne peuvent pas s'offrir de cadeaux mutuellement."
        )
        user_manager.set_spouse(user_id, spouse_user_id)

    await query.edit_message_text(text=text, reply_markup=markup)  # type: ignore


async def gift_button(query: CallbackQuery) -> None:
    """Parses the CallbackQuery and updates the message text from wish inline keyboard.
    data is like 'wish <giftee_id> <wish_index>'
    """
    data = await query.data.split(" ", 2)
    logger.info("gift query data: %s", data)
    giftee = int(data[1])
    wish_index = int(data[2])

    reply = set_wish_giver(
        user_id=giftee,
        wish_index=wish_index,
        giver=query.from_user.id,
    )
    await query.edit_message_text(text=reply)


async def inline_button_pressed(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text
    from people and wish inline keyboards."""
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise.
    # See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    keyboard_type = await query.data.split(" ")[0]
    logger.info("keyboard query data: %s", keyboard_type)

    if keyboard_type == "cancel":
        text = "🙅 Opération annulée."
        await query.edit_message_text(text=text)
        return

    if keyboard_type == "user":
        user_button(query)
        return

    if keyboard_type == "wish":
        gift_button(query)
        return


def build_wishes_inline_kb(username: str) -> InlineKeyboardMarkup:
    """build an inline keyboard based on user wishes."""
    user = UserManager().search_user(username)
    tkeyboard = [
        InlineKeyboardButton(
            wish.wish,
            callback_data="wish " + str(user.tg_id) + " " + str(index),
        )
        for index, wish in enumerate(user.wishes)
    ]
    tkeyboard.append(InlineKeyboardButton("Annuler", callback_data="cancel 0 cancel"))
    # split keyboard in two columns
    keyboard = [tkeyboard[i : i + COLUMNS] for i in range(0, len(tkeyboard), COLUMNS)]
    return InlineKeyboardMarkup(keyboard)


def register_keyboards(application: Application) -> None:
    """Register all the keyboards in the application."""
    application.add_handler(CommandHandler("register", register_inline_kb))
    application.add_handler(CommandHandler("unregister", unregister_inline_kb))
    application.add_handler(CommandHandler("spouse", spouse_inline_kb))
    application.add_handler(CommandHandler("offrir", giftee_inline_kb))
    # TODO: implement this command
    # application.add_handler(CommandHandler("reprendre", gift_inline_kb))

    # handle all inline keyboards responses
    application.add_handler(CallbackQueryHandler(inline_button_pressed))
