#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

from logging import getLogger

from telegram import (
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    CallbackContext,
)

from flantier import _santa
from flantier._keyboards import build_people_inline_kb
from flantier._users import UserManager

logger = getLogger("flantier")


def wishes(update: Update, _: CallbackContext) -> None:
    """Send a message with user wishes as inline buttons attached."""
    keyboard = build_people_inline_kb("wishes")
    update.message.reply_text(
        "🤷 De qui veux tu consulter la liste de souhaits? 🤷", reply_markup=keyboard
    )


def update_wishes_list(update: Update, context: CallbackContext) -> None:
    """Met à jour la liste des cadeaux."""
    _santa.create_missing_users()
    _santa.update_wishes_list()
    text = "🎁 liste des cadeaux mise à jour 🎁"
    context.bot.send_message(chat_id=update.message.chat_id, text=text)
    logger.info(text)


# LEGACY
#########


def comments(update: Update, context: CallbackContext) -> None:
    """Affiche la liste de cadeaux et les commentaires associés d'une personne."""
    if len(update.message.text.split(" ")) > 1:
        name = update.message.text.split(" ")[1]

        reply_del_kb = ReplyKeyboardRemove()
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=_santa.find_wishes(update.message.from_user.id, name),
            reply_markup=reply_del_kb,
        )

    else:
        _keyboards.build_people_keyboard("/commentaires")


def add_gifter(tg_id: int, message: list) -> str:
    """Ajoute un offrant à un cadeau.
    vérifie que la personne existe et la disponiblité du cadeau
    """
    participants = UserManager().users
    name, cadeau_index = message

    # trouve le destinataire dans la liste des participants
    if any(qqun.name == name for qqun in participants):
        _wishes = _santa.find_wishes(tg_id, name, table=True)

        if len(_wishes) > 0 and len(_wishes) >= cadeau_index:
            receiver_index = next(
                (i for i, qqun in enumerate(participants) if qqun.name == name),
                -1,
            )

            if participants[receiver_index].donor[cadeau_index] is None:
                text = "Tu offres désormais " + _wishes[cadeau_index - 1] + " à " + name
                # ajoute l'id de l'offrant dans la liste des souhaits du destinataire
                participants[receiver_index].donor[cadeau_index] = tg_id

                # ajoute la place du destinataire et du cadeau
                # dans la liste offer_to de l'offrant
                donor_index = next(
                    (i for i, qqun in enumerate(participants) if qqun.tg_id == tg_id),
                    -1,
                )
                participants[donor_index].offer_to.append((receiver_index, cadeau_index))

            elif participants[receiver_index].donor[cadeau_index] == tg_id:
                text = f"Tu offres déjà {_wishes[cadeau_index - 1]} à {name}"

            else:
                text = (
                    f"Quelqu'un d'autre offre déjà {_wishes[cadeau_index - 1]} à {name}"
                )

        else:
            text = "Je ne trouve pas le cadeau dont tu parles..."
    else:
        text = "Je ne trouve pas la personne dont tu parles..."

    return text


def offer(update: Update, context: CallbackContext) -> None:
    """Permet de sélectionner un cadeau à offrir."""
    message = update.message.text.split(" ")
    # aucun argument fourni
    if len(message) == 1:
        _keyboards.build_people_keyboard("/offrir")
        return

    # fourni que le nom
    if len(message) == 2:
        name = message[1]
        if any(qqun.name == name for qqun in UserManager().users):
            _keyboards.build_wish_keyboard(update, context, name)
        else:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="Je ne trouve pas la personne dont tu parles...",
            )
        return

    # fourni le nom et le numéro
    if len(update.message.text.split(" ")) == 3:
        text = add_gifter(update.message.from_user.id, message)

    # on comprend rien
    else:
        text = "Enfin! Parle Français: /offrir Prénom Numéro_Cadeau"

    reply_del_kb = ReplyKeyboardRemove()
    context.bot.send_message(
        chat_id=update.message.chat_id, text=text, reply_markup=reply_del_kb
    )


def dont_offer(update: Update, context: CallbackContext) -> None:
    """Annule la réservation d'un cadeau à offrir.

    trouver tous les cadeaux qu'on offre
    implémenter la find wishes pour le offer to
    proposer de les annuler
    """
    participants = UserManager().users

    if len(update.message.text.split(" ")) != 3:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Voici la liste des cadeaux que tu offres. Lequel veux-tu supprimer?",
        )
        _keyboards.build_present_keyboard(update, context)

    else:
        reply_del_kb = ReplyKeyboardRemove()
        offrant = next(
            qqun for qqun in participants if qqun.tg_id == update.message.from_user.id
        )
        command = update.message.text.split(" ")
        receiver_index = int(command[1])
        cadeau_index = int(command[2])

        if any(
            offrande
            for offrande in offrant.offer_to
            if offrande == (receiver_index, cadeau_index)
        ):
            offrande_index = next(
                (
                    i
                    for i, offrande in enumerate(offrant.offer_to)
                    if offrande == (int(command[1]), int(command[2]))
                ),
                -1,
            )

            del offrant.offer_to[offrande_index]
            participants[receiver_index].donor[cadeau_index] = None

            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="Cadeau supprimé",
                reply_markup=reply_del_kb,
            )
        else:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="Impossible de trouver le cadeau spécifié...",
                reply_markup=reply_del_kb,
            )
