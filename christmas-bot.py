#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

from random import choice
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Filters,
    Updater,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
)
import configs
import flantier
import logging
import sys
import santa
import keyboards
import users
from roulette import Roulette

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
            text=f"🎉 Bravo {update.message.from_user.first_name} 🎉\nTu es bien enregistré.e pour le tirage au sort.",
        )

    elif not_registered == -1:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"🦋 Patience {update.message.from_user.first_name},\n🙅 les inscriptions n'ont pas encore commencées ou sont déjà terminées!",
        )

    elif not_registered == -2:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"{update.message.from_user.first_name}, petit coquinou! Tu t'es déjà inscrit.e. Si tu veux recevoir un deuxième cadeau, tu peux te faire un auto-cadeau 🤷🔄🎁",
        )


def unregister(update: Update, context: CallbackContext):
    """Permet de se désinscrire du tirage au sort."""
    roulette = Roulette()

    if roulette.remove_user(update.message.from_user.id):
        text = f"🗑 {update.message.from_user.first_name} a bien été retiré.e du tirage au sort."
    else:
        text = f"🤷 {update.message.from_user.first_name} n'a jamais été inscrit.e au tirage au sort..."

    context.bot.send_message(chat_id=update.message.chat_id, text=text)


def list_users(update: Update, context: CallbackContext):
    """Liste les participants inscrits."""
    roulette = Roulette()
    users = roulette.list_users()

    if len(users):
        text = "🙋 Les participant.e.s sont: \n" + users
    else:
        text = ("😢 Aucun.e participant.e n'est encore inscrit.e.",)

    context.bot.send_message(chat_id=update.message.chat_id, text=text)


def get_result(update: Update, context: CallbackContext):
    roulette = Roulette()
    supplier = roulette.get_user(update.message.from_user.id)
    receiver = roulette.get_user(supplier["dest"])

    context.bot.send_message(chat_id=update.message.from_user.id, text=f"🎅 Youpi tu offres à : {receiver['name']} 🎁\n")


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


def offer(update: Update, context: CallbackContext):
    """Permet de sélectionner un cadeau à offrir."""

    roulette = Roulette()
    # aucun argument fourni
    if len(update.message.text.split(" ")) == 1:
        keyboards.build_people_keyboard(update, context, offer_flag=True)

    # fourni que le nom
    elif len(update.message.text.split(" ")) == 2:
        name = update.message.text.split(" ")[1]
        if any([qqun for qqun in roulette.participants if (qqun.name == name)]):
            keyboards.build_wish_keyboard(update, context, name)
        else:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="Je ne trouve pas la personne dont tu parles...",
            )

    # fourni le nom et le numéro
    elif len(update.message.text.split(" ")) == 3:

        # doit vérifier que la personne existe
        # doit vérifier que le cadeau existe et est disponible
        name = update.message.text.split(" ")[1]
        cadeau_index = int(update.message.text.split(" ")[2])

        # trouve le destinataire dans la liste des participants
        if any(qqun.name == name for qqun in roulette.participants):
            wishes = santa.find_wishes(update.message.from_user.id, name, table=True)

            if len(wishes) > 0 and len(wishes) >= cadeau_index:
                receiver_index = next(
                    (
                        i
                        for i, qqun in enumerate(roulette.participants)
                        if qqun.name == name
                    ),
                    -1,
                )

                if roulette.participants[receiver_index].donor[cadeau_index] is None:
                    text = (
                        "Tu offres désormais " + wishes[cadeau_index - 1] + " à " + name
                    )
                    # ajoute l'id de l'offrant dans la liste des souhaits du destinataire
                    roulette.participants[receiver_index].donor[
                        cadeau_index
                    ] = update.message.from_user.id

                    # ajoute la place du destinataire et du cadeau dans la liste offer_to de l'offrant
                    donor_index = next(
                        (
                            i
                            for i, qqun in enumerate(roulette.participants)
                            if qqun.tg_id == update.message.from_user.id
                        ),
                        -1,
                    )
                    roulette.participants[donor_index].offer_to.append(
                        (receiver_index, cadeau_index)
                    )

                elif (
                    roulette.participants[receiver_index].donor[cadeau_index]
                    == update.message.from_user.id
                ):
                    text = f"Tu offres déjà {wishes[cadeau_index - 1]} à {name}"

                else:
                    text = f"Quelqu'un d'autre offre déjà {wishes[cadeau_index - 1]} à {name}"

            else:
                text = "Je ne trouve pas le cadeau dont tu parles..."
        else:
            text = "Je ne trouve pas la personne dont tu parles..."

        reply_del_kb = ReplyKeyboardRemove()
        context.bot.send_message(
            chat_id=update.message.chat_id, text=text, reply_markup=reply_del_kb
        )

    # on comprend rien
    else:
        reply_del_kb = ReplyKeyboardRemove()
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Enfin! Parle Français: /offrir Prénom Numéro_Cadeau",
            reply_markup=reply_del_kb,
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

    Args:
        bot (TYPE): telegram bot
        tid (int): telegram id to check

    Returns:
        bool: whether the telegram user is admin of the bot or not
    """
    if update.message.from_user.id == configs.admin:
        return True
    else:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"🙅 Petit.e canaillou! Tu ne possèdes pas ce pouvoir.",
        )
        return False


def open_registrations(update: Update, context: CallbackContext):
    """Lance la campagne d'inscription."""
    if is_admin(update, context):
        Roulette().inscriptions_open = True
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="🎉 Les inscriptions sont ouvertes 🎉\n🎅 Vous pouvez désormais vous inscrire en envoyant /participer",
        )


def close_registrations(update: Update, context: CallbackContext):
    """Termine la campagne d'inscription."""
    if is_admin(update, context):
        Roulette().inscriptions_open = False
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="🙅 Les inscriptions sont fermées 🙅\n🎁 C'est bientôt l'heure des résultats",
        )


def add_exclusion(update: Update, context: CallbackContext):
    # provide names supplier and forbidden recipient
    # else display people keyboard
    roulette = Roulette()

    keyboards.build_exclude_keyboard(update, context, roulette.participants)
    supplier = roulette.search_user("TUTU")

    context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Qui ne doit pas offrir à qui? Selectionne la personne a qui iel ne peut pas offrir:",
    )
    forbidden_recipient = 0

    if roulette.exclude(supplier, forbidden_recipient):
        context.bot.send_message(chat_id=update.message.chat_id, text=f"c'est bon")
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text=f"impossibru")


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
                receiver = roulette.get_user(user["dest"])
                context.bot.send_message(
                    user["tg_id"], text=f"🎅 Youpi tu offres à : {receiver['name']} 🎁\n"
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


def backup_state(update: Update, context: CallbackContext):
    """Sauvegarde l'état de flantier dans un fichier."""
    santa.backup_cadeaux()

    text = "État de Flantier sauvegardé\n"
    context.bot.send_message(chat_id=update.message.chat_id, text=text)
    logger.info(text)


def restore_state(bot, update):
    """Restaure l'état de flantier sauvegardé dans un fichier."""
    Roulette().participants = santa.load_cadeaux()

    text = "État de Flantier restauré\n"
    context.bot.send_message(chat_id=update.message.chat_id, text=text)
    logger.info(text)


############
# BOT CODE #
############


def init_christmas():
    roulette = Roulette()
    roulette.inscriptions_open = False
    roulette.load_users()


def start(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "C'est bientôt Noël! Je suis là pour vous aider à organiser tout ça Larmina mon p'tit. Je tire au sort les cadeaux et vous nous faites une jolie table avec une bonne bûche pour le dessert."
        ),
    )
    help(update, context)


def help(update: Update, context: CallbackContext):
    simple_help = """Voici les commandes disponibles:
/aide - affiche cette aide
/bonjour - je vous dirai bonjour à ma manière
/participer - s'inscrire pour le secret santa
/retirer - se désinscrire du secret santa
/liste - donne la liste des participants
/resultat - donne le résultat tu tirage au sort en dm

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

    if configs.extended_mode:
        help_text = simple_help + extended_help
    else:
        help_text = simple_help

    context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)


def hello(update: Update, context: CallbackContext):
    """Petit Comique."""
    context.bot.send_message(
        chat_id=update.message.chat_id, text=choice(flantier.citations)
    )


def unknown_command(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Le Mue... quoi? Je n'ai pas compris cette commande.",
    )


def register_commands(dispatcher):
    # users commands
    dispatcher.add_handler(CommandHandler("bonjour", hello))
    dispatcher.add_handler(CommandHandler("hello", hello))
    dispatcher.add_handler(CommandHandler("participer", register))
    dispatcher.add_handler(CommandHandler("register", register))
    dispatcher.add_handler(CommandHandler("retirer", unregister))
    dispatcher.add_handler(CommandHandler("remove", unregister))
    dispatcher.add_handler(CommandHandler("liste", list_users))
    dispatcher.add_handler(CommandHandler("list", list_users))
    dispatcher.add_handler(CommandHandler("resultat", get_result))
    dispatcher.add_handler(CommandHandler("result", get_result))
    dispatcher.add_handler(CommandHandler("aide", help))
    dispatcher.add_handler(CommandHandler("help", help))

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
    dispatcher.add_handler(CommandHandler("exclude", add_exclusion))

    if configs.extended_mode:
        dispatcher.add_handler(CommandHandler("update", update_wishes_list))
        dispatcher.add_handler(CommandHandler("backup", backup_state))
        dispatcher.add_handler(CommandHandler("restore", restore_state))

    # unkown commands
    dispatcher.add_handler(MessageHandler(Filters.command, unknown_command))


def error(update: Update, context: CallbackContext):
    """Bot error handler."""
    logger.warning('Update "%s" caused error "%s"' % (update, context.error))


def main():
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


if __name__ == "__main__":
    main()
