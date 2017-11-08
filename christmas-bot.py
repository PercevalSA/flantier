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


def build_people_keyboard(bot, update, offer_flag=False, comments=False):
    """Créer le clavier avec les noms des participants"""
    
    if offer_flag:
        button_list = ["/offrir " + qqun.name for qqun in participants]
    elif comments:
        button_list = ["/commentaires " + qqun.name for qqun in participants]
    else:
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

    if offer_flag:
        text = "À qui veux-tu offrir ?"
    else:
        text = "De qui veux-tu afficher la liste de souhaits ?"
    
    bot.send_message(chat_id=update.message.chat_id, text=text, reply_markup=reply_keyboard)


def build_wish_keyboard(bot, update, name):
    destinataire = next(qqun for qqun in participants if qqun.name == name)
    
    i = 1
    button_list = []
    while(destinataire.wishes[i] != None):
        button_list.append("/offrir " + name + " " + str(i))
        i += 1

    header_buttons=None
    footer_buttons=["/annuler"]
    n_cols = 2

    menu = [button_list[i:i + n_cols] for i in range(0, len(button_list), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)

    reply_keyboard = ReplyKeyboardMarkup(keyboard=menu, one_time_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id, text="Quel cadeau veux tu offrir ?", 
        reply_markup=reply_keyboard)


# COMMANDES

def start(bot, update):
    """Lance la campagne d'inscription"""
    global inscriptions

    if (update.message.from_user.id != administrateur.tg_id):
        bot.send_message(chat_id=update.message.chat_id,
            text="C'est {} l'administrateur, petit canaillou !"
            .format(administrateur.name))
    else:
        inscriptions = True
        bot.send_message(chat_id=update.message.chat_id,
            text="Tu peux directement t'inscrire en envoyant /participer")

def stop(bot, update):
    """Arrête la campagne d'inscription"""
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
        build_people_keyboard(bot, update)


def comments(bot, update):
    """Affiche les cadeaux et les commentaires"""
    if(len(update.message.text.split(' ')) > 1):
        name = update.message.text.split(' ')[1]
        
        reply_del_kb = ReplyKeyboardRemove()
        bot.send_message(chat_id=update.message.chat_id, 
            text=find_wishes(update.message.from_user.id, name, with_comments=True),
            reply_markup=reply_del_kb)

    else:
        build_people_keyboard(bot, update, comments=True)

def offer(bot, update):
    """Permet de selectionner un cadeau à offrir"""

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
        cadeau = int(update.message.text.split(' ')[2])

        if any(qqun.name == name for qqun in participants):
            
            wishes = find_wishes(update.message.from_user.id, name, table=True)

            if len(wishes) > 0 and len(wishes) >= cadeau:
                index = next((i for i, qqun in enumerate(participants) if qqun.name == name), -1)

                if participants[index].offre[cadeau] == None:
                    text = "Tu offres désormais " + wishes[cadeau] + " à " + name
                    participants[index].offre[cadeau] = update.message.from_user.id

                elif participants[index].offre[cadeau] == update.message.from_user.id:
                    text = "Tu offres déjà " + wishes[cadeau] + " à " + name

                else:
                    text = "Quelqu'un d'autre offre déjà " + wishes[cadeau] + " à " + name

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
    # trouver tous les cadeaux qu'on offre
    # proposer de les annuler
    print("TODO : annuler un cadeau")

def cancel(bot, update):
    reply_del_kb = ReplyKeyboardRemove()
    bot.send_message(chat_id=update.message.chat_id,
        text="Opération d'offrande annulée, Égoïste!", reply_markup=reply_del_kb)


def update(bot, update):
    """Met à jour la liste des cadeaux"""
    init_cadeaux()

def backup(bot, update):
    backup_cadeaux()

def restore(bot, update):
    global participants
    participants = load_cadeaux()


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
    dp.add_handler(CommandHandler('commentaires', comments))
    dp.add_handler(CommandHandler('offrir', offer))
    dp.add_handler(CommandHandler('retirer', dont_offer))
    dp.add_handler(CommandHandler('annuler', cancel))
    dp.add_handler(CommandHandler('backup', backup))
    dp.add_handler(CommandHandler('restore', restore))


    # log all errors
    dp.add_error_handler(error)

    # initialize participants and presents
    global administrateur
    administrateur = init_participants(participants)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
