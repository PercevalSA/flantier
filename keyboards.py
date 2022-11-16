#!/usr/bin/python3

"""GESTION DES CLAVIERS."""

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext
import logging
import roulette

logger = logging.getLogger("flantier")

# to do inline
def build_exclude_keyboard(
    update: Update,
    context: CallbackContext,
    user_list: list,
):
    u"""Créer le clavier avec les noms des participants."""
    button_list = [user['name'] for user in user_list]

    header_buttons = None
    footer_buttons = ["/annuler"]
    n_cols = 2

    menu = [button_list[i: i + n_cols] for i in range(0, len(button_list), n_cols)]
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
    u"""Créer le clavier avec les noms des participants."""
    if offer_flag:
        button_list = ["/offrir " + qqun.name for qqun in roulette.participants]
    elif comments:
        button_list = ["/commentaires " + qqun.name for qqun in roulette.participants]
    else:
        button_list = ["/cadeaux " + qqun.name for qqun in roulette.participants]

    header_buttons = None
    footer_buttons = ["/annuler"]
    n_cols = 2

    menu = [button_list[i: i + n_cols] for i in range(0, len(button_list), n_cols)]
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
    u"""Affiche le clavier des souhaits d'une personne."""
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
        qqun for qqun in roulette.participants if qqun.tg_id == update.message.from_user.id
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
                ] + "\n"
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
            chat_id=update.message.chat_id, text=text, reply_markup=reply_keyboard)
