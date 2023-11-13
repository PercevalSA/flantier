#!/usr/bin/python3

"""gestion des claviers interractifs dans telegram"""

import logging

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import CallbackContext

from flantier._roulette import Roulette
from flantier._users import UserManager

logger = logging.getLogger("flantier")


# pylint: disable=W0613
def inline_kb(update: Update, context: CallbackContext) -> None:
    """Sends a message with three inline buttons attached."""
    keyboard = [
        [InlineKeyboardButton(user.name, callback_data=str(user["tg_id"]))]
        for user in UserManager().users
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Qui ne peut pas offrir à qui?", reply_markup=reply_markup)


# pylint: disable=W0613
def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise.
    # See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    user_manager = UserManager()
    logger.info("Query data %s", query.data)
    user = user_manager.get_user(int(query.data))
    logger.info("User %s", user)

    if user.spouse == 0 and user.giftee == 0:
        text = f"{user.name} peut offrir à tout le monde"
    else:
        text = f"{user.name} ne peut pas offrir à {user.spouse} et à {user.last_giftee}"
    query.edit_message_text(text=text)


# TODO use callback querry handler
# https://github.com/python-telegram-bot/v13.x-wiki/wiki/Code-snippets#build-a-menu-with-buttons
def build_exclude_keyboard(
    update: Update,
    context: CallbackContext,
    user_list: list,
) -> ReplyKeyboardMarkup:
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
    # text = (
    #     "🙅 Qui ne doit pas offrir à qui? 🙅\n"
    #     "Selectionne la personne qui n'a pas le droit d'offrir à quelqu'un"
    # )
    # context.bot.send_message(
    #     chat_id=update.message.chat_id, text=text, reply_markup=reply_keyboard
    # )


# /exclude => present keyboard with names, force reply to get the name associated with the command
# /exclude name => if no name valid, ask again


# def build_exclude_keyboard(update: Update, context: CallbackContext):


def build_people_keyboard(
    update: Update, context: CallbackContext, command: str = ""
) -> ReplyKeyboardMarkup:
    """Créer le clavier avec les noms des participants. Ajoute la commande en prefix
    /offrir, cadeaux, commentaires, /exclude
    """

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
    #     text = "De qui veux-tu afficher la liste de souhaits ?"


def build_wish_keyboard(update: Update, context: CallbackContext, name: str) -> None:
    """Affiche le clavier des souhaits d'une personne."""
    giftee = next(qqun for qqun in Roulette().participants if qqun.name == name)

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
    roulette = Roulette()

    offrant = next(
        qqun
        for qqun in roulette.participants
        if qqun.tg_id == update.message.from_user.id
    )

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
        text += " [" + roulette.participants[offrant.offer_to[i][0]].name + "] : "
        text += (
            roulette.participants[offrant.offer_to[i][0]].wishes[offrant.offer_to[i][1]]
            + "\n"
        )
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
