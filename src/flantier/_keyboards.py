"""gestion des claviers interractifs dans telegram"""

from logging import getLogger

from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    CallbackContext,
)

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
    filter_registered: bool = False,
) -> InlineKeyboardMarkup:
    """build an inline keyboard based on user names.
    Créer le clavier avec les noms des participants. Ajoute la commande en prefix
    /offrir, /cadeaux, /commentaires, /exclude
    """
    tkeyboard = [
        InlineKeyboardButton(
            user.name,
            callback_data="user "
            + command
            + " "
            + str(user.tg_id)
            + " "
            + str(user.name),
        )
        for user in UserManager().users
        if (not filter_registered or user.registered)
    ]
    tkeyboard.append(InlineKeyboardButton(
        "Annuler", callback_data="cancel 0 cancel"))
    # split keyboard in two columns
    keyboard = [tkeyboard[i: i + COLUMNS]
                for i in range(0, len(tkeyboard), COLUMNS)]
    return InlineKeyboardMarkup(keyboard)


def spouse_inline_kb(update: Update, _: CallbackContext) -> None:
    """Send a message with user spouse as inline buttons attached."""
    keyboard = build_people_inline_kb("wishes")
    logger.info("wishes keyboard")
    update.message.reply_text(
        "De qui veux tu configurer le/la partenaire?", reply_markup=keyboard
    )


def giftee_inline_kb(update: Update, _: CallbackContext) -> None:
    """Send a message with user wishes as inline buttons attached."""
    keyboard = build_people_inline_kb("offer")
    logger.info("giftee keyboard")
    update.message.reply_text("À qui veux-tu offrir ?", reply_markup=keyboard)


def user_button(query: CallbackQuery) -> None:
    """Parses the CallbackQuery and updates the message text from people inline keyboard.
    data is like "user <command> <user_id> <user_name>
    """
    data = query.data.split(" ", 3)
    logger.info("keyboard query data: %s", data)
    command = data[1]
    user_id = int(data[2])
    user_name = data[3]
    markup = None

    if command == "constaints":
        text = UserManager().get_user_constraints(user_id)

    if command == "wishes":
        text = user_wishes_message(user_name)

    if command == "comments":
        text = user_comments_message(user_name)

    if command == "offer":
        text = "Que veux tu offrir comme cadeau ?"
        markup = build_wishes_inline_kb(user_name)

    # TODO  "/commentaires, /exclude"
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

    user_manager = UserManager()
    user = user_manager.get_user(giftee)
    user.wishes[wish_index].giver = query.from_user.id
    user_manager.update_user(user)
    query.edit_message_text(
        text="Youpi! Tu offres " +
        user.wishes[wish_index].wish + " à " + user.name
    )


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
    tkeyboard.append(InlineKeyboardButton(
        "Annuler", callback_data="cancel 0 cancel"))
    # split keyboard in two columns
    keyboard = [tkeyboard[i: i + COLUMNS]
                for i in range(0, len(tkeyboard), COLUMNS)]
    return InlineKeyboardMarkup(keyboard)


# LEGACY
#########
def build_present_keyboard(update: Update, context: CallbackContext) -> None:
    """Affiche le clavier des cadeau que l'on souhaite offrir."""
    users = UserManager().users

    offrant = next(qqun for qqun in users if qqun.tg_id ==
                   update.message.from_user.id)

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
        text += users[offrant.offer_to[i][0]
                      ].wishes[offrant.offer_to[i][1]] + "\n"
        button_list.append(
            f"/retirer {str(offrant.offer_to[i][0])} {str(offrant.offer_to[i][1])}"
        )

        header_buttons = None
        footer_buttons = ["/annuler"]
        n_cols = 2

        menu = [button_list[i: i + n_cols]
                for i in range(0, len(button_list), n_cols)]
        if header_buttons:
            menu.insert(0, header_buttons)
        if footer_buttons:
            menu.append(footer_buttons)

        reply_keyboard = ReplyKeyboardMarkup(
            keyboard=menu, one_time_keyboard=True)

        context.bot.send_message(
            chat_id=update.message.chat_id, text=text, reply_markup=reply_keyboard
        )
