"""gestion des claviers interractifs dans telegram"""

from logging import getLogger
from typing import Any

from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Dispatcher,
)

from flantier._commands_admin import is_admin
from flantier._roulette import Roulette
from flantier._santa import user_comments_message, user_wishes_message
from flantier._users import UserManager

logger = getLogger("flantier")

COLUMNS = 2


# call back data allow to identify the command the user wants to execute
# we set in callback the command and the user id (and name) to execute the command on
# filter_registered is used as logic implication which is equivalent to (not A or B)
# https://fr.wikipedia.org/wiki/Table_de_v%C3%A9rit%C3%A9#Implication_logique
def build_people_inline_kb(
    command: str,
    extra_data: Any = None,
    filter_registered: bool = False,
) -> InlineKeyboardMarkup:
    """build an inline keyboard based on user names.
    Créer le clavier avec les noms des participants. Ajoute la commande en prefix
    /offrir, /cadeaux, /commentaires, /exclude
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


def spouse_inline_kb(update: Update, context: CallbackContext) -> None:
    """Send a message with user spouse as inline buttons attached."""
    if not is_admin(update, context):
        update.message.reply_text("🙅 Tu n'as pas les droits pour cette commande.")
        return

    keyboard = build_people_inline_kb("spouse", filter_registered=True)
    logger.info("spouse keyboard built")
    update.message.reply_text(
        "👬 De qui veux tu configurer le ou la partenaire?", reply_markup=keyboard
    )


def giftee_inline_kb(update: Update, _: CallbackContext) -> None:
    """Send a message with user wishes as inline buttons attached."""
    keyboard = build_people_inline_kb("offer")
    logger.info("giftee keyboard built")
    update.message.reply_text("🎁 À qui veux-tu offrir ?", reply_markup=keyboard)


def register_inline_kb(update: Update, _: CallbackContext) -> None:
    """Send a message with user names as inline buttons attached."""
    keyboard = build_people_inline_kb("register")
    logger.info("register keyboard built")
    update.message.reply_text("✍️ Qui veux-tu inscrire ?", reply_markup=keyboard)


def user_button(query: CallbackQuery) -> None:
    """Parses the CallbackQuery and updates the message text from people inline keyboard.
    data is like "user <command> <user_id> <user_name>
    """
    data = query.data.split(" ")
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
            text = f"❌ impossible d'inscrire {user_name} au tirage au sort. Vérifiez que les inscriptions sont ouvertes."
    if command == "wishes":
        text = user_wishes_message(user_name)

    if command == "comments":
        text = user_comments_message(user_name)

    if command == "offer":
        text = "🎁 Que veux tu offrir comme cadeau ?"
        markup = build_wishes_inline_kb(user_name)

    if command == "spouse":
        text = f"💁 Qui est le ou la partenaire de {user_name}? Iel ne pourra pas lui offrir."
        markup = build_people_inline_kb(
            "exclude", extra_data=user_id, filter_registered=True
        )

    if command == "exclude":
        spouse_user_id = int(data[3])
        spouse_name = user_manager.get_user(spouse_user_id).name
        text = f"👭 {user_name} et {spouse_name} sont partenaires"
        user_manager.set_spouse(user_id, spouse_user_id)

    logger.info("response: %s", text)
    query.edit_message_text(text=text, reply_markup=markup)


def gift_button(query: CallbackQuery) -> None:
    """Parses the CallbackQuery and updates the message text from wish inline keyboard.
    data is like 'wish <giftee_id> <wish_index>'
    """
    data = query.data.split(" ", 2)
    logger.info("gift query data: %s", data)
    giftee = int(data[1])
    wish_index = int(data[2])

    reply = set_wish_giver(
        user_id=giftee,
        wish_index=wish_index,
        giver=query.from_user.id,
    )
    query.edit_message_text(text=reply)


def inline_button_pressed(update: Update, _: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text
    from people and wish inline keyboards."""
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise.
    # See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    keyboard_type = query.data.split(" ")[0]
    logger.info("keyboard query data: %s", keyboard_type)

    if keyboard_type == "cancel":
        text = "🙅 Opération annulée."
        query.edit_message_text(text=text)
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


def register_keyboards(dispatcher: Dispatcher) -> None:
    """Register all the keyboards in the dispatcher."""
    dispatcher.add_handler(CommandHandler("partenaire", spouse_inline_kb))
    dispatcher.add_handler(CommandHandler("offrir", giftee_inline_kb))
    dispatcher.add_handler(CommandHandler("register", register_inline_kb))
    # dispatcher.add_handler(CommandHandler("retirer", gift_inline_kb))

    # handle all inline keyboards responses
    dispatcher.add_handler(CallbackQueryHandler(inline_button_pressed))


# LEGACY
#########
def build_present_keyboard(update: Update, context: CallbackContext) -> None:
    """Affiche le clavier des cadeau que l'on souhaite offrir."""
    users = UserManager().users

    offrant = next(qqun for qqun in users if qqun.tg_id == update.message.from_user.id)

    text = ""
    button_list = []

    if (len(offrant.offer_to)) == 0:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Tu n'offres encore aucun cadeau, égoïste !",
        )
        return

    for i, _ in enumerate(offrant.offer_to):
        text += str(offrant.offer_to[i][0]) + " " + str(offrant.offer_to[i][1])
        text += " [" + users[offrant.offer_to[i][0]].name + "] : "
        text += users[offrant.offer_to[i][0]].wishes[offrant.offer_to[i][1]] + "\n"
        button_list.append(
            f"/retirer {str(offrant.offer_to[i][0])} {str(offrant.offer_to[i][1])}"
        )

        header_buttons = None
        footer_buttons = ["/annuler"]
        n_cols = 2

        menu = [button_list[i : i + n_cols] for i in range(0, len(button_list), n_cols)]
        if header_buttons:
            menu.insert(0, header_buttons)
        if footer_buttons:
            menu.append(footer_buttons)

        reply_keyboard = ReplyKeyboardMarkup(keyboard=menu, one_time_keyboard=True)

        context.bot.send_message(
            chat_id=update.message.chat_id, text=text, reply_markup=reply_keyboard
        )
