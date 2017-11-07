#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Herr Flantier der Geschenk Manager

import logging
from telegram.ext import Updater, CommandHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from random import choice, shuffle
from flantier import *

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def tirage():
    """algorithme de tirage au sort, complète automatique les champs 'dest'"""
    # init
    global imp_total
    imp_total = []

    for qqun in participants:
        qqun.dest = 0

    print("\nC'est parti !!!\n")

    # mélange
    shuffle(participants)

    # attribution
    for quelquun in participants:

        # determine la liste des possibles
        possibles = []
        for possibilite in participants:
            if(possibilite in imp_total or possibilite in quelquun.impossible):
                continue
            else:
                possibles.append(possibilite)

        # s'il n'y a pas de solution on redémarre
        if len(possibles) == 0:
            print("\nOn recommence !!!\n")
            return -1

        # selectionne qqun
        quelquun.dest = choice(possibles)
        # l'ajoute aux tirés"
        imp_total.append(quelquun.dest)
        # passe au suivant

    print("\nC'est fini !!!\n")

    return 0


def find_wishes(tg_id, name):
    """Trouve et retourne la liste de souhaits avec le nom de la personne"""
    matches = [qqun for qqun in participants if (qqun.name == name)]

    if(len(matches) == 0):
        return "Je n'ai trouvé personne correspondant à ta recherche. N'oublie pas la majuscule."

    if(matches[0].tg_id == tg_id):
        return  "Hop hop hop ! Tu ne peux pas consulter ta propre liste de cadeaux, ça gacherait la surprise."

    souhaits = ""
    for i in range (1, len(matches[0].wishes)):
        souhaits += str(i) + " : " + matches[0].wishes[i] + "\n"

    if len(souhaits) == 0:
        souhaits = name + " n'a rien demandé pour Noël :'("

    return souhaits


def build_keyboard(bot, update):
    """Créer le clavier avec les noms des participants et force la réposne"""
    
    button_list = ["/cadeaux " + qqun.name for qqun in participants]
    header_buttons=None
    footer_buttons=None
    n_cols = 2

    menu = [button_list[i:i + n_cols] for i in range(0, len(button_list), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)

    reply_keyboard = ReplyKeyboardMarkup(keyboard=menu, one_time_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id, 
        text="De qui voulez-vous afficher la liste de souhaits ?",
        reply_markup=reply_keyboard)


# COMMANDES

def start(bot, update):
    """lance la campagne d'inscription"""
    global inscriptions

    print(type(administrateur))
    print(administrateur)
    if (update.message.from_user.id != administrateur.tg_id):
        bot.send_message(chat_id=update.message.chat_id,
            text="C'est {} l'administrateur, petit canaillou !"
            .format(administrateur.name))
    else:
        inscriptions = True
        bot.send_message(chat_id=update.message.chat_id,
            text="Vous pouvez directement vous inscrire en envoyant /participer")

def stop(bot, update):
    """arrête la campagne d'inscription"""
    global inscriptions

    if(update.message.from_user.id != administrateur.tg_id):
        bot.send_message(chat_id=update.message.chat_id,
            text="C'est {} l'administrateur, petit canaillou !"
            .format(administrateur.name))
    else:
        inscriptions = False
        bot.send_message(chat_id=update.message.chat_id,
            text="Les inscriptions sont fermées, c'est bientôt l'heure des résultats ! ;)")


def register(bot, update):
    """Permet de s'inscrire au tirage au sort"""
    
    if(inscriptions == True):

        # récupère l'id et ajoute le participant au fichier
        with open(PARTICIPANTS, 'a') as file:
            file.write(str(update.message.from_user.id)
                       + ":"
                       + update.message.from_user.first_name
                       + "\n")

        print("Inscription de : " + update.message.from_user.first_name + " : " 
            + str(update.message.from_user.id))
        
        bot.send_message(chat_id=update.message.chat_id,
            text="Bravo {}, tu es bien enregistré pour le tirage au sort. :)"
            .format(update.message.from_user.first_name))

    else:
        bot.send_message(chat_id=update.message.chat_id,
            text="Patience {}, les inscriptions n'ont pas encore commencé !"
            .format(update.message.from_user.first_name))


def process(bot, update):
    """Lance le tirage au sort et envoie les réponse en message privé"""
    
    # check admin
    if (update.message.from_user.id != administrateur.tg_id):
        bot.send_message(chat_id=update.message.chat_id,
            text="C'est {} l'administrateur, petit canaillou !\n"
            .format(administrateur.name)
            + "Pour participer, envoyez moi la commande /participer")
    else:
        if(inscriptions == True):
            bot.send_message(chat_id=update.message.chat_id,
                text="Les inscriptions ne sont pas encore terminées.")
        else:
            # tant que le tirage ne fonctionne pas on relance
            while (tirage() != 0):
                continue

        # on envoie les résultats en message privé
        for qqun in participants:
            bot.send_message(qqun.tg_id,
                text="Youpi tu offres à : {}\n".format(qqun.dest.name))


def liste(bot, update):
    """Liste les participants inscrits"""
    
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
    """Lance la procédure de recherche et d'affichage des cadeaux"""
    if(len(update.message.text.split(' ')) > 1):
        name = update.message.text.split(' ')[1]
        
        reply_del_kb = ReplyKeyboardRemove()
        bot.send_message(chat_id=update.message.chat_id, 
            text=find_wishes(update.message.from_user.id, name),
            reply_markup=reply_del_kb)

    else:
        build_keyboard(bot, update)


def update_presents(bot, update):
    """Met à jour la liste des cadeaux"""
    if (update.message.from_user.id != administrateur.tg_id):
        bot.send_message(chat_id=update.message.chat_id,
            text="C'est {} l'administrateur, petit canaillou !"
            .format(administrateur.name))
    else:
        init_cadeaux()
        backup_cadeaux()


def hello(bot, update):
    """Petit Comique !"""
    bot.send_message(chat_id=update.message.chat_id, text=choice(citations))


def error(bot, update, error):
    """bot error handler"""
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('stop', stop))
    dp.add_handler(CommandHandler('participer', register))
    dp.add_handler(CommandHandler('bonjour', hello))
    dp.add_handler(CommandHandler('liste', liste))
    dp.add_handler(CommandHandler('tirage', process))
    dp.add_handler(CommandHandler('cadeaux', wishes))
    dp.add_handler(CommandHandler('geschenk', update_presents))

    # log all errors
    dp.add_error_handler(error)

    # initialize participants and presents
    init_participants(administrateur, participants)
    backup_cadeaux()

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
