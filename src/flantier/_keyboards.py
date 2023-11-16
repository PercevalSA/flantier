#!/usr/bin/python3

"""gestion des claviers interractifs dans telegram"""

from logging import getLogger

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Dispatcher,
)

from flantier._santa import get_wish_list
from flantier._users import UserManager

logger = getLogger("flantier")

COLUMNS = 2


def get_user_constraints(user_id: int) -> str:
    user_manager = UserManager()
    user = user_manager.get_user(user_id)
    logger.debug("searching for %s constraints", user)

    if user.spouse == 0 and user.last_giftee == 0:
        text = f"{user.name} peut offrir à tout le monde"
    if user.spouse == 0 or user.last_giftee == 0:
        try:
            constraint = user_manager.get_user(user.spouse)
        except RuntimeError as e:
            logger.error(e)
        try:
            constraint = user_manager.get_user(user.last_giftee)
        except RuntimeError as e:
            logger.error(e)

        text = f"{user.name} ne peut pas offrir à {constraint.name}"
    else:
        text = (
            f"{user.name} ne peut pas offrir à {user_manager.get_user(user.spouse).name} "
            f"et à {user_manager.get_user(user.last_giftee).name}"
        )

    return text


# call back data allow to identify the command the user wants to execute
# we set in callback the command and the user id (and name) to execute the command on
# filter_registered is used as logic implication which is equivalent to (not A or B)
# https://fr.wikipedia.org/wiki/Table_de_v%C3%A9rit%C3%A9#Implication_logique
def build_inline_kb(
    command: str,
    filter_registered: bool = False,
) -> InlineKeyboardMarkup:
    """build an inline keyboard based on user names."""
    keyboard = [
        InlineKeyboardButton(
            user.name,
            callback_data=command + " " + str(user.tg_id) + " " + str(user.name),
        )
        for user in UserManager().users
        if (not filter_registered or user.registered)
    ]

    # split keyboard in two columns
    keyboard = [keyboard[i : i + COLUMNS] for i in range(0, len(keyboard), COLUMNS)]
    return InlineKeyboardMarkup(keyboard)


def contraints_inline_kb(update: Update, _: CallbackContext) -> None:
    """Send a message with user constraints as inline buttons attached."""
    keyboard = build_inline_kb("constaints", filter_registered=True)
    logger.info("constraints")
    update.message.reply_text(
        "De qui veux tu afficher les contraintes?", reply_markup=keyboard
    )


def wishes_inline_kb(update: Update, _: CallbackContext) -> None:
    """Send a message with user wishes as inline buttons attached."""
    keyboard = build_inline_kb("wishes")
    logger.info("wishes")
    update.message.reply_text(
        "De qui veux tu consulter la liste de souhaits?", reply_markup=keyboard
    )


def user_button(update: Update, _: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise.
    # See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    data = query.data.split(" ", 3)
    logger.info("keyboard query data: %s", data)
    command = data[0]
    user_id = int(data[1])
    user_name = data[2]

    if command == "constaints":
        text = get_user_constraints(user_id)

    if command == "wishes":
        wishes = get_wish_list(UserManager().search_user(user_name))
        text = f"🎅 {user_name} voudrait pour Noël:\n" + wishes
        if not wishes:
            text = f"🎅 {user_name} ne veut rien pour Noël 🫥"

    logger.info("response: %s", text)
    query.edit_message_text(text=text)


def register_keyboards(dispatcher: Dispatcher) -> None:
    """Register all inline keyboards."""
    dispatcher.add_handler(CommandHandler("contraintes", contraints_inline_kb))
    dispatcher.add_handler(CommandHandler("cadeaux", wishes_inline_kb))
    dispatcher.add_handler(CallbackQueryHandler(user_button))


def cancel(update: Update, context: CallbackContext) -> None:
    """Cancel current operation and reset flantier state."""
    reply_del_kb = ReplyKeyboardRemove()
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text="🙅 Opération annulée.",
        reply_markup=reply_del_kb,
    )


# TODO use callback querry handler
# https://github.com/python-telegram-bot/v13.x-wiki/wiki/Code-snippets#build-a-menu-with-buttons
def build_exclude_keyboard(user_list: list) -> ReplyKeyboardMarkup:
    """Créer le clavier avec les noms des participants."""
    button_list = [f"/exclude {user.name}" for user in user_list]

    header_buttons = None
    footer_buttons = ["/annuler"]
    n_cols = 2

    menu = [button_list[i : i + n_cols] for i in range(0, len(button_list), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)

    return ReplyKeyboardMarkup(keyboard=menu, one_time_keyboard=True)


def build_people_keyboard(command: str = "") -> ReplyKeyboardMarkup:
    """Créer le clavier avec les noms des participants. Ajoute la commande en prefix
    /offrir, /cadeaux, /commentaires, /exclude
    """
    command = command + " "

    button_list = [command + u.name for u in UserManager().users]
    header_buttons = None
    footer_buttons = ["/annuler"]
    n_cols = 2

    menu = [button_list[i : i + n_cols] for i in range(0, len(button_list), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)

    return ReplyKeyboardMarkup(keyboard=menu, one_time_keyboard=True)

    # if command == "/offrir":
    #     text = "À qui veux-tu offrir ?"
    # else:


def build_wish_keyboard(update: Update, context: CallbackContext, name: str) -> None:
    """Affiche le clavier des souhaits d'une personne."""
    giftee = next(qqun for qqun in UserManager().users if qqun.name == name)

    i = 1
    button_list = []
    while giftee.wishes[i] is not None:
        button_list.append("/offrir " + name + " " + str(i))
        i += 1

    header_buttons = None
    footer_buttons = ["/annuler"]
    n_cols = 2

    menu = [button_list[j : j + n_cols] for j in range(0, len(button_list) - 1, n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)

    reply_keyboard = ReplyKeyboardMarkup(keyboard=menu, one_time_keyboard=True)
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Quel cadeau veux tu offrir ?",
        reply_markup=reply_keyboard,
    )


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
