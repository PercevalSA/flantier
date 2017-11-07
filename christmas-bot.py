#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Herr Flantier der Geschenk Manager

import logging
from telegram.ext import Updater, CommandHandler
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

# COMMANDES

def start(bot, update):
    """lance la campagne d'inscription"""
    global inscriptions

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
    """Affiche les souhaits du participant passé en argument"""    
    if(len(update.message.text.split(' ')) > 1):
        name = update.message.text.split(' ')[1]
        print(name)
        
        matches = [qqun for qqun in participants if (qqun.name == name)]
        
        if(len(matches) == 0):
            bot.send_message(chat_id=update.message.chat_id,
                text="Je n'ai trouvé personne correspondant à ta recherche. N'oublie pas la majuscule.")
            return

        if(matches[0].tg_id == update.message.from_user.id):
            bot.send_message(chat_id=update.message.chat_id,
                text="Hop hop hop ! Tu ne peux pas consulter ta propre liste de cadeaux, ça gacherai la surprise.")
            return

        cadeaux = ""
        for i in range (1, len(matches[0].cadeaux)):
            cadeaux += str(i) + " : " + matches[0].cadeaux[i] + "\n"
        bot.send_message(chat_id=update.message.chat_id, text=cadeaux)        
    
    else:
        bot.send_message(chat_id=update.message.chat_id,
            text="Donnez moi le nom d'un personne avec la commande que je puisse faire quelque chose enfin !")


def update_presents(bot, update):
    """Met à jour la liste des cadeaux"""
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
    dp.add_handler(CommandHandler('maj', update_presents))

    # log all errors
    dp.add_error_handler(error)

    # initialize participants and presents
    init_participants()

    # TODO change
    #init_cadeaux()
    #backup_cadeaux()
    load_cadeaux()

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
