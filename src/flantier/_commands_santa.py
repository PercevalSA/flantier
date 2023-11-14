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

from flantier import _keyboards, _santa
from flantier._roulette import Roulette
from flantier._users import UserManager

logger = getLogger("flantier")


def wishes(update: Update, context: CallbackContext) -> None:
    """Affiche la liste de cadeaux d'une personne."""
    #

    if not context.args:
        logger.info("no name given, displaying user list as keyboard")
        people_kb = _keyboards.build_people_keyboard(update, context, "/cadeaux")
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="🤷 De qui veux-tu afficher la liste de souhaits ? 🤷",
            reply_markup=people_kb,
        )
        return

    # we join all args in order to search for kids name in db which can have spaces
    name = " ".join(context.args)
    logger.info("displaying wishes for %s", name)
    text = _santa.get_wish_list(UserManager().search_user(name).tg_id)
    if not text:
        text = f"🎅 {name} ne veut rien pour Noël 🫥"

    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=text,
        reply_markup=ReplyKeyboardRemove(),
    )


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
        _keyboards.build_people_keyboard(update, context, command="/commentaires")


def add_gifter(tg_id: int, message: list) -> str:
    """Ajoute un offrant à un cadeau.
    vérifie que la personne existe et la disponiblité du cadeau
    """

    roulette = Roulette()
    name, cadeau_index = message

    # trouve le destinataire dans la liste des participants
    if any(qqun.name == name for qqun in roulette.participants):
        _wishes = _santa.find_wishes(tg_id, name, table=True)

        if len(_wishes) > 0 and len(_wishes) >= cadeau_index:
            receiver_index = next(
                (i for i, qqun in enumerate(roulette.participants) if qqun.name == name),
                -1,
            )

            if roulette.participants[receiver_index].donor[cadeau_index] is None:
                text = "Tu offres désormais " + _wishes[cadeau_index - 1] + " à " + name
                # ajoute l'id de l'offrant dans la liste des souhaits du destinataire
                roulette.participants[receiver_index].donor[cadeau_index] = tg_id

                # ajoute la place du destinataire et du cadeau
                # dans la liste offer_to de l'offrant
                donor_index = next(
                    (
                        i
                        for i, qqun in enumerate(roulette.participants)
                        if qqun.tg_id == tg_id
                    ),
                    -1,
                )
                roulette.participants[donor_index].offer_to.append(
                    (receiver_index, cadeau_index)
                )

            elif roulette.participants[receiver_index].donor[cadeau_index] == tg_id:
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


def offer(update: Update, context: CallbackContext):
    """Permet de sélectionner un cadeau à offrir."""

    roulette = Roulette()
    message = update.message.text.split(" ")
    # aucun argument fourni
    if len(message) == 1:
        _keyboards.build_people_keyboard(update, context, offer_flag=True)
        return

    # fourni que le nom
    if len(message) == 2:
        name = message[1]
        if any(qqun.name == name for qqun in roulette.participants):
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


def dont_offer(update: Update, context: CallbackContext):
    """Annule la réservation d'un cadeau à offrir.

    trouver tous les cadeaux qu'on offre
    implémenter la find wishes pour le offer to
    proposer de les annuler
    """
    roulette = Roulette()

    if len(update.message.text.split(" ")) != 3:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Voici la liste des cadeaux que tu offres. Lequel veux-tu supprimer?",
        )
        _keyboards.build_present_keyboard(update, context)

    else:
        reply_del_kb = ReplyKeyboardRemove()
        offrant = next(
            qqun
            for qqun in roulette.participants
            if qqun["tg_id"] == update.message.from_user.id
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
            roulette.participants[receiver_index].donor[cadeau_index] = None

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
