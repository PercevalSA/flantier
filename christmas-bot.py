#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# CHRISTMAS BOT

import logging
from telegram.ext import Updater, CommandHandler
from random import choice, shuffle
from pprint import pprint
import flantier


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram bot token
TOKEN= ""
# file to store users data
FILE = "tirage.dat"

participants = {}

administrateur = 0
admin_name = ""
group = 0


def noel(bot):

    global disponibles

    # je lis les conditions
    bot.send_message(chat_id=group, text="il y a " + str(len(participants)) + " participants :\n" + ", ".join(participants.keys()))

    # tirage au sort
    bot.send_message(chat_id=group, text="Le tirage au sort à été lancé !!")

    # tirage
    ok = False
    while not ok:

        offrants = list(participants.keys())
        recevants = list(participants.keys())
        shuffle(recevants)
        ok = True

        # check les doublons
        for i in range(len(offrants)):
            if offrants[i] == recevants[i]:
                ok = False


    # annonce des résultats
    for i in range(len(offrants)):
        bot.send_message(chat_id=participants[offrants[i]], text = "Youpi ! Cette année tu offres à " + recevants[i])

    bot.send_message(chat_id=group, text="Youhou, les résultats sont tombés ! Allez voir vos petits messages privés pour savoir à qui vous offrez ;)")



# lance le bot
def start(bot, update):
    global administrateur, admin_name, group

    if (update.message.chat.type != "group"):
        bot.send_message(chat_id=update.message.chat_id, text="Merci de me démarrer à partir du groupe de participant pour que je puisse lire les conditions")
    else:
        if(administrateur == 0):
            administrateur = update.message.from_user.id
            admin_name = update.message.from_user.first_name
            group = update.message.chat_id
            bot.send_message(chat_id=update.message.chat_id, text="Bonjour à tous, je m'appel Flantier, je serai votre bot de noël :)\n\n" +
                                                                  "je m'occupe du tirage au sort des cadeaux. Pour cela veuillez m'envoyer \"/participer\" en message privé.")
            bot.send_message(chat_id=update.message.chat_id, text="Pour m'envoyer un message privé cliquez sur ma tête puis sur \"send message\" on l'icône en forme de bulle.")

        else:
            bot.send_message(chat_id=update.message.chat_id, text="C'est {} l'administrateur, petit canaillou !\nPour participer, envoyez moi la commande /participer".format(admin_name) )


def liste(bot, update):

    users = ""
    i = 0

    for personne in participants.keys():
        users += personne + "\n"
        i += 1

    if(len(users) == 0):
        bot.send_message(chat_id=update.message.chat_id, text="Il n'y a encore aucun participant inscrit")
    else:
        bot.send_message(chat_id=update.message.chat_id, text="il y a " + str(i) + " participant(s) inscrit(s) : \n" + users)


def hello(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=choice(flantier.citations))

def bye(bot, update):
    if(update.message.from_user.id != administrateur):
        bot.send_message(chat_id=update.message.chat_id, text="C'est {} l'administrateur, petit canaillou ! Tu ne te débarrasseras pas de moi comme ça !".format(admin_name))
    else:
        bot.send_message(chat=group, text="c'est tout pour moi, adieu !")

def register(bot, update):

    # s'il n'y a pas d'admin les cadeaux ont pas commencés :
    # todo vérifier l'init plutot
    if(administrateur != 0):

        # si le message est en privé c'est bon
        if (update.message.chat.type == "private"):

            # récupère le prénom de l'utilisateur et vérifie s'il est déjà inscrit sinon on l'inscrit
            if (update.message.from_user.first_name in participants):
                bot.send_message(chat_id=update.message.chat_id, text="Pas de panique {}, tu es déjà inscrit ;)".format(update.message.from_user.first_name))
            else:
                # récupère l'id du chat privé et ajoute un participant à la liste
                participants[update.message.from_user.first_name] = update.message.chat.id
                bot.send_message(chat_id=update.message.chat_id, text="Bravo {}, tu es bien enregistré pour le tirage au sort. :)".format(update.message.from_user.first_name))
                pprint(update.message.from_user.first_name + " est inscrit : " + str(update.message.chat_id))
        # sinon on demande expressement un PM
        else:
            bot.send_message(chat_id=update.message.chat_id, text="Bonjour {}, ".format(update.message.from_user.first_name) +
                                                                  "pourrais tu m'écrire en privé s'il te plait \n" +
                                                                  "pour que personne ne sache à qui tu offres ^^")
    else:
        bot.send_message(chat_id=update.message.chat_id, text="Patience {}, les inscriptions n'ont pas encore commencés !".format(update.message.from_user.first_name))

# lance le tirage au sort, envoie les réponses et termine
# todo mettre une vérification du nombre d'inscrits ou mettre un clavier pour valider
def process(bot, update):
    if (update.message.chat.type != "group" or group == 0):
        bot.send_message(chat_id=update.message.chat_id, text="Le tirage doit être lancé depuis le groupe pour que tous le monde soit au courant !")
    else:
        if(update.message.from_user.id != administrateur):
            bot.send_message(chat_id=update.message.chat_id, text="C'est {} l'administrateur, petit canaillou !\nPour participer, envoyez moi la commande /participer".format(admin_name))
        else:
            noel(bot)


# bot error handler
def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('liste', liste))
    dp.add_handler(CommandHandler('bonjour', hello))
    dp.add_handler(CommandHandler('aurevoir', bye))
    dp.add_handler(CommandHandler('participer', register))
    dp.add_handler(CommandHandler('tirage', process))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
