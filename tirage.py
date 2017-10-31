#!/usr/local/bin/python3

from pprint import pprint
from random import choice

# variables
# todo recupérer les participants das inscrits
liste = ["User1", "User2", "User3"]
participants = []
nb_participants = len(liste)
nb_cadeaux = 2

# resultat
repartition = {}

# dictionnaire pour le lien avec telegram
telegram_ids = {}

# dictionnaire pour le tirage au sort : personnes restant à tirer
disponible = {}



def initialisation():
    telegram_ids['user1'] = 00000  # prenom:tg_id

    for i in liste:
        disponible[i] = nb_cadeaux

    # presentation
    print("il y a " + str(nb_participants) + " participants :")
    for i in liste:
        print("    " + i)
    print("chacun offre a " + str(nb_cadeaux) + " personnes")


# ajoute un participant à la liste
def ajouter(participant):
    if(participant in participants):
        return -1
    else:
        participants.append(participant)
        return 0

def noel():
    initialisation()

    for i in liste:
        repartition[i] = tirage(i)

    pprint(repartition)

    exit()


# retourne un tableau des personnes à qui offrir
def tirage(offrant):

    # les personnes à qui offrir
    recevants = []
    for i in range(nb_cadeaux):
        recevants.append(offrant)

    # tant que la liste des recevants n'est pas conforme
    while(offrant in recevants                 # test si l'offrant est dans les receveurs
          or len(set(recevants)) != nb_cadeaux # test les doublons
          or not sont_disponibles(recevants)): # test si les recevants sont disponibles

        # set tous les recevants aléatoirement
        for i in range(nb_cadeaux):
            recevants[i] = choice(liste)

    # déduis les disponibilités
    for i in range(nb_cadeaux):
        disponible[recevants[i]] -= 1

    return recevants


# test la disponibilité des recevants
def sont_disponibles(recevants):
    for i in recevants:
        if disponible[i] == 0:
            return False

    return True
