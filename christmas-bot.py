#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

from random import choice
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Filters, Updater, CallbackContext, CommandHandler, MessageHandler
import configs
import flantier
import logging
import sys
import telegram

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger("flantier")

########################
# GESTION DES CLAVIERS #
########################


def build_people_keyboard(update: Update, context: CallbackContext, offer_flag=False, comments=False):
    """Créer le clavier avec les noms des participants."""
    if offer_flag:
        button_list = ["/offrir " + qqun.name for qqun in participants]
    elif comments:
        button_list = ["/commentaires " + qqun.name for qqun in participants]
    else:
        button_list = ["/cadeaux " + qqun.name for qqun in participants]

    header_buttons = None
    footer_buttons = ["/annuler"]
    n_cols = 2

    menu = [button_list[i:i + n_cols] for i in range(0, len(button_list), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)

    reply_keyboard = ReplyKeyboardMarkup(keyboard=menu, one_time_keyboard=True)

    if offer_flag:
        text = "À qui veux-tu offrir ?"
    else:
        text = "De qui veux-tu afficher la liste de souhaits ?"

    context.bot.send_message(chat_id=update.message.chat_id, text=text, reply_markup=reply_keyboard)


def build_wish_keyboard(update: Update, context: CallbackContext, name):
    """Affiche le clavier des souhaits d'une personne."""
    destinataire = next(qqun for qqun in participants if qqun.name == name)

    i = 1
    button_list = []
    while(destinataire.wishes[i] is not None):
        button_list.append("/offrir " + name + " " + str(i))
        i += 1

    header_buttons = None
    footer_buttons = ["/annuler"]
    n_cols = 2

    menu = [button_list[j:j + n_cols] for j in range(0, len(button_list) - 1, n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)

    reply_keyboard = ReplyKeyboardMarkup(keyboard=menu, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.message.chat_id,
                     text="Quel cadeau veux tu offrir ?",
                     reply_markup=reply_keyboard)


def build_present_keyboard(update: Update, context: CallbackContext):
    """Affiche le clavier des cadeau que l'on souhaite offrir."""
    offrant = next(qqun for qqun in participants if qqun.tg_id == update.message.from_user.id)

    text = ""
    button_list = []

    if(len(offrant.offer_to)) == 0:
        context.bot.send_message(chat_id=update.message.chat_id,
                         text="Tu n'offres encore aucun cadeau, égoïste !")
        return

    else:

        for i in range(0, len(offrant.offer_to)):
            text += str(offrant.offer_to[i][0]) + " " + str(offrant.offer_to[i][1])
            text += " [" + participants[offrant.offer_to[i][0]].name + "] : "
            text += participants[offrant.offer_to[i][0]].wishes[offrant.offer_to[i][1]] + "\n"
            button_list.append("/retirer " + str(offrant.offer_to[i][0]) + " " + str(offrant.offer_to[i][1]))

        header_buttons = None
        footer_buttons = ["/annuler"]
        n_cols = 2

        menu = [button_list[i:i + n_cols] for i in range(0, len(button_list), n_cols)]
        if header_buttons:
            menu.insert(0, header_buttons)
        if footer_buttons:
            menu.append(footer_buttons)

        reply_keyboard = ReplyKeyboardMarkup(keyboard=menu, one_time_keyboard=True)

        context.bot.send_message(chat_id=update.message.chat_id, text=text,
            reply_markup=reply_keyboard)


#########################
# COMMANDES UTILISATEUR #
#########################

def hello(update: Update, context: CallbackContext):
    """Petit Comique."""
    context.bot.send_message(chat_id=update.message.chat_id, text=choice(flantier.citations))


def register(update: Update, context: CallbackContext):
    """Permet de s'inscrire au tirage au sort."""
    if(flantier.inscriptions):

        # récupère l'id et ajoute le participant au fichier
        with open(configs.PARTICIPANTS, 'a') as file:
            file.write(str(update.message.from_user.id)
                       + ":"
                       + update.message.from_user.first_name
                       + "\n")

        logger.info("Inscription de : " + update.message.from_user.first_name + " : "
            + str(update.message.from_user.id))

        context.bot.send_message(chat_id=update.message.chat_id,
            text="Bravo {}, tu es bien enregistré pour le tirage au sort. :)"
            .format(update.message.from_user.first_name))

    else:
        context.bot.send_message(chat_id=update.message.chat_id,
            text="Patience {}, les inscriptions n'ont pas encore commencées ou sont déjà terminées !"
            .format(update.message.from_user.first_name))


def liste(update: Update, context: CallbackContext):
    """Liste les participants inscrits."""
    users = ""
    try:
        with open('participants.txt', 'r') as file:
            for line in file:
                users += line

        if(len(users) != 0):
            context.bot.send_message(chat_id=update.message.chat_id,
                text="Les participants sont : \n" + users)
        else:
            raise FileNotFoundError

    except FileNotFoundError:
        context.bot.send_message(chat_id=update.message.chat_id,
            text="Il n'y a encore aucun participant inscrit.")


def wishes(update: Update, context: CallbackContext):
    """Affiche la liste de cadeaux d'une personne."""
    if(len(update.message.text.split(' ')) > 1):
        name = update.message.text.split(' ')[1]

        reply_del_kb = ReplyKeyboardRemove()
        context.bot.send_message(chat_id=update.message.chat_id,
            text=find_wishes(update.message.from_user.id, name),
            reply_markup=reply_del_kb)

    else:
        build_people_keyboard(update, context)


def comments(update: Update, context: CallbackContext):
    """Affiche la liste de cadeaux et les commentaires associés d'une personne."""
    if(len(update.message.text.split(' ')) > 1):
        name = update.message.text.split(' ')[1]

        reply_del_kb = ReplyKeyboardRemove()
        context.bot.send_message(chat_id=update.message.chat_id, 
            text=find_wishes(update.message.from_user.id, name, with_comments=True),
            reply_markup=reply_del_kb)

    else:
        build_people_keyboard(update, context, comments=True)


def offer(update: Update, context: CallbackContext):
    """Permet de sélectionner un cadeau à offrir"""
    # aucun argument fourni
    if(len(update.message.text.split(' ')) == 1):
        build_people_keyboard(update, context, offer_flag=True)

    # fourni que le nom
    elif(len(update.message.text.split(' ')) == 2):
        name = update.message.text.split(' ')[1]
        if any([qqun for qqun in participants if (qqun.name == name)]):
            build_wish_keyboard(update, context, name)
        else:
            context.bot.send_message(chat_id=update.message.chat_id,
                text="Je ne trouve pas la personne dont tu parles...")


    # fourni le nom et le numéro
    elif(len(update.message.text.split(' ')) == 3):

        # doit vérifier que la personne existe
        # doit vérifier que le cadeau existe et est disponible
        name = update.message.text.split(' ')[1]
        cadeau_index = int(update.message.text.split(' ')[2])

        # trouve le destinataire dans la liste des participants
        if any(qqun.name == name for qqun in participants):
            wishes = find_wishes(update.message.from_user.id, name, table=True)

            if len(wishes) > 0 and len(wishes) >= cadeau_index:
                receiver_index = next((i for i, qqun in enumerate(participants) if qqun.name == name), -1)

                if participants[receiver_index].donor[cadeau_index] is None:
                    text = "Tu offres désormais " + wishes[cadeau_index - 1] + " à " + name
                    # ajoute l'id de l'offrant dans la liste des souhaits du destinataire
                    participants[receiver_index].donor[cadeau_index] = update.message.from_user.id

                    # ajoute la place du destinataire et du cadeau dans la liste offer_to de l'offrant
                    donor_index = next((i for i, qqun in enumerate(participants)
                        if qqun.tg_id == update.message.from_user.id ), -1)
                    participants[donor_index].offer_to.append((receiver_index, cadeau_index))

                elif participants[receiver_index].donor[cadeau_index] == update.message.from_user.id:
                    text = "Tu offres déjà " + wishes[cadeau_index - 1] + " à " + name

                else:
                    text = "Quelqu'un d'autre offre déjà " + wishes[cadeau_index - 1] + " à " + name

            else:
                text = "Je ne trouve pas le cadeau dont tu parles..."
        else:
            text = "Je ne trouve pas la personne dont tu parles..."

        reply_del_kb = ReplyKeyboardRemove()
        context.bot.send_message(chat_id=update.message.chat_id, text=text, reply_markup=reply_del_kb)

    # on comprend rien
    else:
        reply_del_kb = ReplyKeyboardRemove()
        context.bot.send_message(chat_id=update.message.chat_id,
            text="Enfin! Parle Français: /offrir Prénom Numéro_Cadeau", reply_markup=reply_del_kb)


def dont_offer(update: Update, context: CallbackContext):
    """Annule la réservation d'un cadeau à offrir.

    trouver tous les cadeaux qu'on offre
    implémenter la find wishes pour le offer to
    proposer de les annuler
    """
    if(len(update.message.text.split(' ')) != 3):
        context.bot.send_message(chat_id=update.message.chat_id,
            text="Voici la liste des cadeaux que tu offres. Lequel veux-tu supprimer?")
        build_present_keyboard(update, context)

    else:
        reply_del_kb = ReplyKeyboardRemove()
        offrant = next(qqun for qqun in participants if qqun.tg_id == update.message.from_user.id)
        command = update.message.text.split(' ')
        receiver_index = int(command[1])
        cadeau_index = int(command[2])

        if any(offrande for offrande in offrant.offer_to if offrande == (receiver_index, cadeau_index)):
            offrande_index = next((i for i, offrande in enumerate(offrant.offer_to) if offrande == (int(command[1]), int(command[2]))), -1)

            del offrant.offer_to[offrande_index]
            participants[receiver_index].donor[cadeau_index] = None

            context.bot.send_message(chat_id=update.message.chat_id,
                text="Cadeau supprimé", reply_markup=reply_del_kb)
        else:
            context.bot.send_message(chat_id=update.message.chat_id,
                text="Impossible de trouver le cadeau spécifié...", reply_markup=reply_del_kb)


def cancel(update: Update, context: CallbackContext):
    reply_del_kb = ReplyKeyboardRemove()
    context.bot.send_message(chat_id=update.message.chat_id,
                     text="Opération annulée.", reply_markup=reply_del_kb)


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
    if update.message.from_user.id == configs.administrateur.tg_id:
        return True
    else:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"C'est {configs.administrateur.name} l'administrateur, petit canaillou !"
        )
        return False


def christmas(update: Update, context: CallbackContext):
    """Lance la campagne d'inscription."""
    global inscriptions

    if is_admin(update, context):
        inscriptions = True
        context.bot.send_message(chat_id=update.message.chat_id,
                         text="Tu peux directement t'inscrire en envoyant /participer")


def stop(update: Update, context: CallbackContext):
    """Termine la campagne d'inscription."""
    global inscriptions

    if is_admin(update, context):
        inscriptions = False
        context.bot.send_message(chat_id=update.message.chat_id,
                         text="Les inscriptions sont fermées, c'est bientôt l'heure des résultats ! ;)")


def process(update: Update, context: CallbackContext):
    """Lance le tirage au sort et envoie les réponses en message privé."""

    if is_admin(update, context):
        if(inscriptions):
            context.bot.send_message(chat_id=update.message.chat_id,
                             text="Les inscriptions ne sont pas encore terminées.")
        else:
            # tant que le tirage ne fonctionne pas on relance
            while (tirage() != 0):
                continue

        # on envoie les résultats en message privé
        for qqun in participants:
            context.bot.send_message(qqun.tg_id,
                             text="Youpi tu offres à : {}\n"
                             .format(qqun.dest.name))


def update_wishes_list(update: Update, context: CallbackContext):
    u"""Met à jour la liste des cadeaux."""
    if get_cadeaux():
        text = "liste des cadeaux inchangée\n"
    else:
        text = "liste des cadeaux mise à jour\n"

    context.bot.send_message(chat_id=update.message.chat_id, text=text)
    logger.info(text)


def backup_state(update: Update, context: CallbackContext):
    """Sauvegarde l'état de flantier dans un fichier."""
    backup_cadeaux()

    text = "État de Flantier sauvegardé\n"
    context.bot.send_message(chat_id=update.message.chat_id, text=text)
    logger.info(text)


def restore_state(bot, update):
    """Restaure l'état de flantier sauvegardé dans un fichier."""
    global participants
    participants = load_cadeaux()

    text = "État de Flantier restauré\n"
    context.bot.send_message(chat_id=update.message.chat_id, text=text)
    logger.info(text)

############
# BOT CODE #
############


def init_christmas():
    # initialize participants and presents
    flantier.init_participants(flantier.participants)


def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=(u"C'est bientôt Noël! Je suis là pour vous aider à organiser tout ça Larmina mon p'tit. Je tire sort les cadeaux et vous nous faites une jolie table avec une bonne bûche pour le dessert."))

def help(update: Update, context: CallbackContext):
    help_text = """Voici les commandes disponibles:
    /bonjour        je vous dirai bonjour à ma manière
    /participer     s'inscrire pour le secret santa
    /liste          donne la liste des participants
    /cadeaux        donne la liste des voeux de cadeaux
    /commentaires   donne les commentaires associés aux voeux
    /offrir         reserver un cadeau à offrir (pour que personne d'autre ne l'offre)
    /retirer        annuler la réservation
    /annuler        annuler l'opération en cours
    """
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)


def unknown_command(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def register_commands(dispatcher):
    # users commands
    dispatcher.add_handler(CommandHandler('bonjour', hello))
    dispatcher.add_handler(CommandHandler('participer', register))
    dispatcher.add_handler(CommandHandler('liste', liste))
    dispatcher.add_handler(CommandHandler('cadeaux', wishes))
    dispatcher.add_handler(CommandHandler('commentaires', comments))
    dispatcher.add_handler(CommandHandler('offrir', offer))
    dispatcher.add_handler(CommandHandler('retirer', dont_offer))
    dispatcher.add_handler(CommandHandler('annuler', cancel))
    dispatcher.add_handler(CommandHandler('aide', help))
    dispatcher.add_handler(CommandHandler('help', help))

    # admin commands
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('noel', christmas))
    dispatcher.add_handler(CommandHandler('stop', stop))
    dispatcher.add_handler(CommandHandler('tirage', process))
    dispatcher.add_handler(CommandHandler('update', update_wishes_list))
    dispatcher.add_handler(CommandHandler('backup', backup_state))
    dispatcher.add_handler(CommandHandler('restore', restore_state))

    # unkown commands
    dispatcher.add_handler(MessageHandler(Filters.command, unknown_command))

# def error(bot, update, error):
#     """Bot error handler."""
#     logger.warning('Update "%s" caused error "%s"' % (update, error))


def main():
    # Create the EventHandler and pass it your bot's token
    updater = Updater(token=configs.TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # answer in Telegram on different commands
    register_commands(dispatcher)

    # # log all errors
    # dispatcher.add_error_handler(error)

    init_christmas()

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
