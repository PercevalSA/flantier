#!/usr/bin/python3

"""GESTION DES CLAVIERS."""

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import CallbackContext
import logging
from roulette import Roulette

logger = logging.getLogger("flantier")


def inline_kb(update: Update, context: CallbackContext) -> None:
    """Sends a message with three inline buttons attached."""
    roulette = Roulette()
    keyboard = [[InlineKeyboardButton(user["name"], callback_data=str(user["tg_id"]))] for user in roulette.participants]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Qui ne peut pas offrir à qui?", reply_markup=reply_markup)


def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    roulette = Roulette()
    print('roulette')
    print(query.data)
    user = roulette.get_user(int(query.data))
    print(user)
    excludes = ""
    if len(user['exclude']) == 0:
        text = f"{user['name']} peut offrir à tout le monde"
    else:
        for u in user['exclude']:
            print(u)
            excludes = excludes + roulette.get_user(u)['name'] + ", "
        text = f"{user['name']} ne peut pas offrir à {excludes}"
    query.edit_message_text(text=text)


# to do inline
def build_exclude_keyboard(
    update: Update,
    context: CallbackContext,
    user_list: list,
):
    """Créer le clavier avec les noms des participants."""
    button_list = [user["name"] for user in user_list]

    header_buttons = None
    footer_buttons = ["/annuler"]
    n_cols = 2

    menu = [button_list[i : i + n_cols] for i in range(0, len(button_list), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)

    reply_keyboard = ReplyKeyboardMarkup(keyboard=menu, one_time_keyboard=True)
    text = "🙅 Qui ne doit pas offrir à qui? 🙅\nSelectionne la personne qui n'a pas le droit d'offrir à quelqu'un."
    context.bot.send_message(
        chat_id=update.message.chat_id, text=text, reply_markup=reply_keyboard
    )


def build_people_keyboard(
    update: Update,
    context: CallbackContext,
    offer_flag=False,
    comments=False,
):
    roulette = Roulette()
    """Créer le clavier avec les noms des participants."""
    if offer_flag:
        button_list = ["/offrir " + qqun.name for qqun in roulette.participants]
    elif comments:
        button_list = ["/commentaires " + qqun.name for qqun in roulette.participants]
    else:
        button_list = ["/cadeaux " + qqun.name for qqun in roulette.participants]

    header_buttons = None
    footer_buttons = ["/annuler"]
    n_cols = 2

    menu = [button_list[i : i + n_cols] for i in range(0, len(button_list), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)

    reply_keyboard = ReplyKeyboardMarkup(keyboard=menu, one_time_keyboard=True)

    if offer_flag:
        text = "À qui veux-tu offrir ?"
    else:
        text = "De qui veux-tu afficher la liste de souhaits ?"

    context.bot.send_message(
        chat_id=update.message.chat_id, text=text, reply_markup=reply_keyboard
    )


def build_wish_keyboard(update: Update, context: CallbackContext, name):
    """Affiche le clavier des souhaits d'une personne."""
    destinataire = next(qqun for qqun in roulette.participants if qqun.name == name)

    i = 1
    button_list = []
    while destinataire.wishes[i] is not None:
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


def build_present_keyboard(update: Update, context: CallbackContext):
    """Affiche le clavier des cadeau que l'on souhaite offrir."""
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

    else:

        for i in range(0, len(offrant.offer_to)):
            text += str(offrant.offer_to[i][0]) + " " + str(offrant.offer_to[i][1])
            text += " [" + roulette.participants[offrant.offer_to[i][0]].name + "] : "
            text += (
                roulette.participants[offrant.offer_to[i][0]].wishes[
                    offrant.offer_to[i][1]
                ]
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
