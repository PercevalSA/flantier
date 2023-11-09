#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

import logging
import os
from pathlib import Path
from random import choice

import configs
import keyboards
import noel_flantier
import santa
from roulette import Roulette
from telegram import (
    ChatAction,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("flantier")

#########################
# COMMANDES UTILISATEUR #
#########################


def register(update: Update, context: CallbackContext):
    """Permet de s'inscrire au tirage au sort."""
    roulette = Roulette()
    not_registered = roulette.add_user(
        tg_id=update.message.from_user.id, name=update.message.from_user.first_name
    )
    if not not_registered:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=(
                f"🎉 Bravo {update.message.from_user.first_name} 🎉\n"
                "Tu es bien enregistré.e pour le tirage au sort"
            ),
        )

    elif not_registered == -1:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=(
                f"🦋 Patience {update.message.from_user.first_name},\n"
                "🙅 les inscriptions n'ont pas encore commencées ou sont déj"
                "à terminées!"
            ),
        )

    elif not_registered == -2:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=(
                f"{update.message.from_user.first_name}, petit coquinou! Tu t'es déjà"
                " inscrit.e. Si tu veux recevoir un deuxième cadeau, tu peux te faire"
                " un auto-cadeau 🤷🔄🎁"
            ),
        )


def unregister(update: Update, context: CallbackContext):
    """Permet de se désinscrire du tirage au sort."""
    roulette = Roulette()

    if roulette.remove_user(update.message.from_user.id):
        text = (
            f"🗑 {update.message.from_user.first_name} "
            "a bien été retiré.e du tirage au sort."
        )
    else:
        text = (
            f"🤷 {update.message.from_user.first_name} "
            "n'a jamais été inscrit.e au tirage au sort..."
        )

    context.bot.send_message(chat_id=update.message.chat_id, text=text)


def list_users(update: Update, context: CallbackContext):
    """Liste les participants inscrits."""
    roulette = Roulette()
    users = roulette.list_users()

    if len(users):
        text = f"🙋 Les participant.e.s sont:\n{users}"
    else:
        text = "😢 Aucun.e participant.e n'est encore inscrit.e."

    context.bot.send_message(chat_id=update.message.chat_id, text=text)

    # on check qu'on a accès aux chats privés de tous les participants
    for user in roulette.participants:
        logger.info("Envoi du message privé à %s", user["name"])
        context.bot.send_message(
            user["tg_id"],
            text="🧪 Test",
        )


def get_result(update: Update, context: CallbackContext):
    """Affiche le résultat du tirage au sort en message privé."""
    roulette = Roulette()
    supplier = roulette.get_user(update.message.from_user.id)
    receiver = roulette.get_user(supplier["giftee"])

    context.bot.send_message(
        chat_id=update.message.from_user.id,
        text=f"🎅 Youpi tu offres à : {receiver['name']} 🎁\n",
    )


######################
# COMMANDES AVANCEES #
######################


def wishes(update: Update, context: CallbackContext):
    """Affiche la liste de cadeaux d'une personne."""
    if len(update.message.text.split(" ")) > 1:
        name = update.message.text.split(" ")[1]

        reply_del_kb = ReplyKeyboardRemove()
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=santa.find_wishes(update.message.from_user.id, name),
            reply_markup=reply_del_kb,
        )

    else:
        keyboards.build_people_keyboard(update, context)


def comments(update: Update, context: CallbackContext):
    """Affiche la liste de cadeaux et les commentaires associés d'une personne."""
    if len(update.message.text.split(" ")) > 1:
        name = update.message.text.split(" ")[1]

        reply_del_kb = ReplyKeyboardRemove()
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=santa.find_wishes(
                update.message.from_user.id, name, with_comments=True
            ),
            reply_markup=reply_del_kb,
        )

    else:
        keyboards.build_people_keyboard(update, context, comments=True)


def add_gifter(tg_id: int, name: str, cadeau_index: int) -> str:
    """Ajoute un offrant à un cadeau.
    vérifie que la personne existe et la disponiblité du cadeau
    """

    roulette = Roulette()

    # trouve le destinataire dans la liste des participants
    if any(qqun.name == name for qqun in roulette.participants):
        _wishes = santa.find_wishes(tg_id, name, table=True)

        if len(_wishes) > 0 and len(_wishes) >= cadeau_index:
            receiver_index = next(
                (
                    i
                    for i, qqun in enumerate(roulette.participants)
                    if qqun.name == name
                ),
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
        keyboards.build_people_keyboard(update, context, offer_flag=True)
        return

    # fourni que le nom
    if len(message) == 2:
        name = message[1]
        if any(qqun.name == name for qqun in roulette.participants):
            keyboards.build_wish_keyboard(update, context, name)
        else:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="Je ne trouve pas la personne dont tu parles...",
            )
        return

    # fourni le nom et le numéro
    if len(update.message.text.split(" ")) == 3:
        text = add_gifter(update.message.from_user.id, message[1], message[2])

    # on comprend rien
    else:
        text = ("Enfin! Parle Français: /offrir Prénom Numéro_Cadeau",)

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
        keyboards.build_present_keyboard(update, context)

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


def cancel(update: Update, context: CallbackContext):
    """Cancel current operation and reset flantier state."""
    reply_del_kb = ReplyKeyboardRemove()
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Opération annulée.",
        reply_markup=reply_del_kb,
    )


############################
# COMMANDES ADMINISTRATEUR #
############################


def is_admin(update: Update, context: CallbackContext) -> bool:
    """check if the given telegram id is admin of the bot

    Returns:
        bool: whether the telegram user is admin of the bot or not
    """
    if update.message.from_user.id != configs.admin:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="🙅 Petit.e canaillou! Tu ne possèdes pas ce pouvoir.",
        )
        return False

    return True


def open_registrations(update: Update, context: CallbackContext):
    """Lance la campagne d'inscription."""
    if is_admin(update, context):
        Roulette().inscriptions_open = True
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=(
                "🎉 Les inscriptions sont ouvertes 🎉\n"
                "🎅 Vous pouvez désormais vous inscrire en envoyant /participer"
            ),
        )


def close_registrations(update: Update, context: CallbackContext):
    """Termine la campagne d'inscription."""
    if is_admin(update, context):
        Roulette().inscriptions_open = False
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=(
                "🙅 Les inscriptions sont fermées 🙅\n"
                "🎁 C'est bientôt l'heure des résultats"
            ),
        )


def add_spouse(update: Update, context: CallbackContext):
    """Ajoute un conjoint à un participant.
    provide names supplier and forbidden recipient else display people keyboard
    """
    roulette = Roulette()

    keyboards.build_exclude_keyboard(update, context, roulette.participants)
    supplier = roulette.search_user("TUTU")

    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=(
            "Qui ne doit pas offrir à qui? Selectionne la personne a qui iel ne peut"
            " pas offrir:"
        ),
    )
    forbidden_recipient = 0

    if roulette.exclude(supplier, forbidden_recipient):
        context.bot.send_message(chat_id=update.message.chat_id, text="c'est bon")
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="impossibru")


# TODO generate exlcusion from last year


def process(update: Update, context: CallbackContext):
    """Lance le tirage au sort et envoie les réponses en message privé."""
    roulette = Roulette()

    if is_admin(update, context):
        if roulette.is_ready():
            # tant que le tirage ne fonctionne pas on relance
            while not roulette.tirage():
                continue

            # on envoie les résultats en message privé
            for user in roulette.participants:
                receiver = roulette.get_user(user["giftee"])
                context.bot.send_message(
                    user["tg_id"],
                    text=f"🎅 Youpi tu offres à : {receiver['name']} 🎁\n",
                )
        else:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="⚠️ Les inscriptions ne sont pas encore terminées. ⚠️",
            )


def update_wishes_list(update: Update, context: CallbackContext):
    """Met à jour la liste des cadeaux."""
    if santa.get_cadeaux():
        text = "liste des cadeaux inchangée\n"
    else:
        text = "liste des cadeaux mise à jour\n"

    context.bot.send_message(chat_id=update.message.chat_id, text=text)
    logger.info(text)


############
# BOT CODE #
############


def init_christmas():
    """Start Christmas: load users and close registrations."""
    roulette = Roulette()
    roulette.inscriptions_open = False
    roulette.load_users()


def start(update: Update, context: CallbackContext):
    """Start the interaction with the bot. Enable the bot to talk to user."""
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "C'est bientôt Noël! Je suis là pour vous aider à organiser tout ça Larmina"
            " mon p'tit. Je tire au sort les cadeaux et vous nous faites une jolie"
            " table avec une bonne bûche pour le dessert."
        ),
    )
    help(update, context)
    logger.info()


def help_message(update: Update, context: CallbackContext):
    """Send the help message with all available commands"""
    simple_help = """Voici les commandes disponibles:
/aide - affiche cette aide
/participer - s'inscrire pour le secret santa
/retirer - se désinscrire du secret santa
/liste - donne la liste des participants
/resultat - donne le résultat tu tirage au sort en dm

/bonjour - je vous dirai bonjour à ma manière
/larmina - le caire nid d'espion
/dolores - rio ne répond plus

Les commandes aussi sont disponibles en anglais:
/help, /hello, /register, /remove, /list, /result
"""

    extended_help = """

/cadeaux - donne la liste des voeux de cadeaux
/commentaires - donne les commentaires associés aux voeux
/offrir - reserve un cadeau à offrir (pour que personne d'autre ne l'offre)
/retirer - annule la réservation
/annuler - annule l'opération en cours
    """

    admin_help = """

Commandes administrateur:
/start - démarre l'interaction avec le bot
/open - ouvre la session d'inscription
/close - termine la session d'inscription
/tirage - lance le tirage au sort avec les contraintes
/exclude - ajoute une contrainte de destinataire (conjoint, année précédente)
"""

    if configs.extended_mode:
        help_text = simple_help + extended_help + admin_help
    else:
        help_text = simple_help + admin_help

    context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)


def hello(update: Update, context: CallbackContext):
    """Petit Comique."""
    context.bot.send_message(
        chat_id=update.message.chat_id, text=choice(noel_flantier.quotes)
    )


def send_audio_quote(chat_id: int, context: CallbackContext, folder: Path):
    """Petit Comique."""
    audio_files = os.listdir(folder)
    audio = folder / Path(choice(audio_files))

    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_AUDIO)
    # pylint: disable=R1732
    context.bot.send_audio(
        chat_id=chat_id, audio=open(audio, "rb"), disable_notification=True
    )


def quote_oss1(update: Update, context: CallbackContext):
    """Petit Comique."""
    send_audio_quote(update.message.chat_id, context, Path("audio/oss1"))


def quote_oss2(update: Update, context: CallbackContext):
    """Petit Comique."""
    send_audio_quote(update.message.chat_id, context, Path("audio/oss2"))


def unknown_command(update: Update, context: CallbackContext):
    """Gère les commandes inconues ou incorrectes"""
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Le Mue... quoi? Je n'ai pas compris cette commande.",
    )


def register_commands(dispatcher):
    """Register all commands."""
    # users commands
    dispatcher.add_handler(CommandHandler("bonjour", hello))
    dispatcher.add_handler(CommandHandler("hello", hello))
    dispatcher.add_handler(CommandHandler("larmina", quote_oss1))
    dispatcher.add_handler(CommandHandler("dolores", quote_oss2))
    dispatcher.add_handler(CommandHandler("participer", register))
    dispatcher.add_handler(CommandHandler("register", register))
    dispatcher.add_handler(CommandHandler("retirer", unregister))
    dispatcher.add_handler(CommandHandler("remove", unregister))
    dispatcher.add_handler(CommandHandler("liste", list_users))
    dispatcher.add_handler(CommandHandler("list", list_users))
    dispatcher.add_handler(CommandHandler("resultat", get_result))
    dispatcher.add_handler(CommandHandler("result", get_result))
    dispatcher.add_handler(CommandHandler("aide", help_message))
    dispatcher.add_handler(CommandHandler("help", help_message))

    if configs.extended_mode:
        dispatcher.add_handler(CommandHandler("cadeaux", wishes))
        dispatcher.add_handler(CommandHandler("commentaires", comments))
        dispatcher.add_handler(CommandHandler("offrir", offer))
        dispatcher.add_handler(CommandHandler("retirer", dont_offer))
        dispatcher.add_handler(CommandHandler("annuler", cancel))

    # admin commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("open", open_registrations))
    dispatcher.add_handler(CommandHandler("close", close_registrations))
    dispatcher.add_handler(CommandHandler("tirage", process))
    dispatcher.add_handler(CommandHandler("exclude", add_spouse))

    if configs.extended_mode:
        dispatcher.add_handler(CommandHandler("update", update_wishes_list))

    # inline kb
    dispatcher.add_handler(CommandHandler("contraintes", keyboards.inline_kb))
    dispatcher.add_handler(CallbackQueryHandler(keyboards.button))

    # unkown commands
    dispatcher.add_handler(MessageHandler(Filters.command, unknown_command))


def error(update: Update, context: CallbackContext):
    """Bot error handler."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token
    updater = Updater(token=configs.TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # answer in Telegram on different commands
    register_commands(dispatcher)

    # log all errors
    dispatcher.add_error_handler(error)

    init_christmas()

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
