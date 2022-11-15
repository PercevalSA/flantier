#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

from random import choice
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CallbackContext, CommandHandler
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


def build_people_keyboard(bot, update, offer_flag=False, comments=False):
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

    bot.send_message(chat_id=update.message.chat_id, text=text, reply_markup=reply_keyboard)


def build_wish_keyboard(bot, update, name):
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
    bot.send_message(chat_id=update.message.chat_id, text="Quel cadeau veux tu offrir ?",
        reply_markup=reply_keyboard)


def build_present_keyboard(bot, update):
    """Affiche le clavier des cadeau que l'on souhaite offrir."""
    offrant = next(qqun for qqun in participants if qqun.tg_id == update.message.from_user.id)

    text = ""
    button_list = []

    if(len(offrant.offer_to)) == 0:
        bot.send_message(chat_id=update.message.chat_id,
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

        bot.send_message(chat_id=update.message.chat_id, text=text,
            reply_markup=reply_keyboard)


#########################
# COMMANDES UTILISATEUR #
#########################

def hello(bot, update):
    """Petit Comique."""
    bot.send_message(chat_id=update.message.chat_id, text=choice(citations))


def register(bot, update):
    """Permet de s'inscrire au tirage au sort."""
    if(inscriptions):

        # récupère l'id et ajoute le participant au fichier
        with open(PARTICIPANTS, 'a') as file:
            file.write(str(update.message.from_user.id)
                       + ":"
                       + update.message.from_user.first_name
                       + "\n")

        logger.info("Inscription de : " + update.message.from_user.first_name + " : "
            + str(update.message.from_user.id))

        bot.send_message(chat_id=update.message.chat_id,
            text="Bravo {}, tu es bien enregistré pour le tirage au sort. :)"
            .format(update.message.from_user.first_name))

    else:
        bot.send_message(chat_id=update.message.chat_id,
            text="Patience {}, les inscriptions n'ont pas encore commencées ou sont déjà terminées !"
            .format(update.message.from_user.first_name))


def liste(bot, update):
    """Liste les participants inscrits."""
    users = ""
    try:
        with open('participants.txt', 'r') as file:
            for line in file:
                users += line

        if(len(users) != 0):
            bot.send_message(chat_id=update.message.chat_id,
                text="Les participants sont : \n" + users)
        else:
            raise FileNotFoundError

    except FileNotFoundError:
        bot.send_message(chat_id=update.message.chat_id,
            text="Il n'y a encore aucun participant inscrit.")


def wishes(bot, update):
    """Affiche la liste de cadeaux d'une personne."""
    if(len(update.message.text.split(' ')) > 1):
        name = update.message.text.split(' ')[1]

        reply_del_kb = ReplyKeyboardRemove()
        bot.send_message(chat_id=update.message.chat_id,
            text=find_wishes(update.message.from_user.id, name),
            reply_markup=reply_del_kb)

    else:
        build_people_keyboard(bot, update)


def comments(bot, update):
    """Affiche la liste de cadeaux et les commentaires associés d'une personne."""
    if(len(update.message.text.split(' ')) > 1):
        name = update.message.text.split(' ')[1]

        reply_del_kb = ReplyKeyboardRemove()
        bot.send_message(chat_id=update.message.chat_id, 
            text=find_wishes(update.message.from_user.id, name, with_comments=True),
            reply_markup=reply_del_kb)

    else:
        build_people_keyboard(bot, update, comments=True)


def offer(bot, update):
    """Permet de sélectionner un cadeau à offrir"""
    # aucun argument fourni
    if(len(update.message.text.split(' ')) == 1):
        build_people_keyboard(bot, update, offer_flag=True)

    # fourni que le nom
    elif(len(update.message.text.split(' ')) == 2):
        name = update.message.text.split(' ')[1]
        if any([qqun for qqun in participants if (qqun.name == name)]):
            build_wish_keyboard(bot, update, name)
        else:
            bot.send_message(chat_id=update.message.chat_id,
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
        bot.send_message(chat_id=update.message.chat_id, text=text, reply_markup=reply_del_kb)

    # on comprend rien
    else:
        reply_del_kb = ReplyKeyboardRemove()
        bot.send_message(chat_id=update.message.chat_id,
            text="Enfin! Parle Français: /offrir Prénom Numéro_Cadeau", reply_markup=reply_del_kb)


def dont_offer(bot, update):
    """Annule la réservation d'un cadeau à offrir.

    trouver tous les cadeaux qu'on offre
    implémenter la find wishes pour le offer to
    proposer de les annuler
    """
    if(len(update.message.text.split(' ')) != 3):
        bot.send_message(chat_id=update.message.chat_id,
            text="Voici la liste des cadeaux que tu offres. Lequel veux-tu supprimer?")
        build_present_keyboard(bot, update)

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

            bot.send_message(chat_id=update.message.chat_id,
                text="Cadeau supprimé", reply_markup=reply_del_kb)
        else:
            bot.send_message(chat_id=update.message.chat_id,
                text="Impossible de trouver le cadeau spécifié...", reply_markup=reply_del_kb)


def cancel(bot, update):
    reply_del_kb = ReplyKeyboardRemove()
    bot.send_message(chat_id=update.message.chat_id,
                     text="Opération annulée.", reply_markup=reply_del_kb)


############################
# COMMANDES ADMINISTRATEUR #
############################


def is_admin(bot, chat_id, user_id: int) -> bool:
    """check if the given telegram id is admin of the bot
    
    Args:
        bot (TYPE): telegram bot
        tid (int): telegram id to check
    
    Returns:
        bool: whether the telegram user is admin of the bot or not
    """
    if user_id == administrateur.tg_id:
        return True
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="C'est {} l'administrateur, petit canaillou !"
                         .format(administrateur.name))
        return False


def christmas(bot, update):
    """Lance la campagne d'inscription."""
    global inscriptions

    if is_admin(bot, update.message.chat_id, update.message.from_user.id):
        inscriptions = True
        bot.send_message(chat_id=update.message.chat_id,
                         text="Tu peux directement t'inscrire en envoyant /participer")


def stop(bot, update):
    """Termine la campagne d'inscription."""
    global inscriptions

    if is_admin(bot, update.message.chat_id, update.message.from_user.id):
        inscriptions = False
        bot.send_message(chat_id=update.message.chat_id,
                         text="Les inscriptions sont fermées, c'est bientôt l'heure des résultats ! ;)")


def process(bot, update):
    """Lance le tirage au sort et envoie les réponses en message privé."""

    if is_admin(bot, update.message.chat_id, update.message.from_user.id):
        if(inscriptions):
            bot.send_message(chat_id=update.message.chat_id,
                             text="Les inscriptions ne sont pas encore terminées.")
        else:
            # tant que le tirage ne fonctionne pas on relance
            while (tirage() != 0):
                continue

        # on envoie les résultats en message privé
        for qqun in participants:
            bot.send_message(qqun.tg_id,
                             text="Youpi tu offres à : {}\n"
                             .format(qqun.dest.name))


def update(bot, update):
    u"""Met à jour la liste des cadeaux."""
    if get_cadeaux():
        text = "liste des cadeaux inchangée\n"
    else:
        text = "liste des cadeaux mise à jour\n"

    bot.send_message(chat_id=update.message.chat_id, text=text)
    logger.info(text)


def backup(bot, update):
    """Sauvegarde l'état de flantier dans un fichier."""
    backup_cadeaux()

    text = "État de Flantier sauvegardé\n"
    bot.send_message(chat_id=update.message.chat_id, text=text)
    logger.info(text)


def restore(bot, update):
    """Restaure l'état de flantier sauvegardé dans un fichier."""
    global participants
    participants = load_cadeaux()

    text = "État de Flantier restauré\n"
    bot.send_message(chat_id=update.message.chat_id, text=text)
    logger.info(text)

############
# BOT CODE #
############


def init_christmas():
    # initialize participants and presents
    global administrateur
    administrateur = flantier.init_participants(flantier.participants)


def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=(u"C'est bientôt Noël! Je suis là pour vous aider à organiser tout ça Larmina mon p'tit. Je tire sort les cadeaux et vous nous faites une jolie table avec une bonne bûche pour le dessert."))


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

    # admin commands
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('noel', christmas))
    dispatcher.add_handler(CommandHandler('stop', stop))
    dispatcher.add_handler(CommandHandler('tirage', process))
    dispatcher.add_handler(CommandHandler('update', update))
    dispatcher.add_handler(CommandHandler('backup', backup))
    dispatcher.add_handler(CommandHandler('restore', restore))


def error(bot, update, error):
    """Bot error handler."""
    logger.warning('Update "%s" caused error "%s"' % (update, error))


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

if __name__ == '__main__':
    main()
