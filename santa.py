#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

import configs
from apiclient.discovery import build
import logging
import pickle
from random import choice

# Global variables
participants = []
imp_total = []
inscriptions = False

logger = logging.getLogger("flantier")


class Personne:
    def __init__(self, tg_id, name):
        self.tg_id = tg_id
        self.name = name
        # liste des personnes à qui la personne ne peut pas offrir
        self.impossible = []
        # personne à qui offrir
        self.dest = None

        # cadeaux qui viennent du google doc
        self.wishes = [None] * configs.nb_cadeaux
        self.comments = [None] * configs.nb_cadeaux
        # liste des personnes qui offrent les cadeaux correspondant
        self.donor = [None] * configs.nb_cadeaux

        # liste de [personne, cadeau] que la personne a décidé d'offrir
        self.offer_to = []


def get_cadeaux():

    service = build("sheets", "v4", credentials=None, developerKey=configs.API_key)
    request = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=configs.spreadsheet_id,
            range=configs.data_range,
            majorDimension="COLUMNS",
        )
    )
    spreadsheet = request.execute()

    values = spreadsheet.get("values")
    # data_json = json.dumps(values, indent=4, ensure_ascii=False)
    new_data_flag = False

    for column in range(0, len(values), 2):
        name = values[column][0]
        index = next(
            (i for i, qqun in enumerate(participants) if qqun.name == name), -1
        )

        # mise à jour de la liste de cadeaux si les élements sont différents
        if index != -1:
            update_flag = False
            # met à jour la liste des cadeaux
            for i in range(0, len(values[column])):
                if participants[index].wishes[i] != values[column][i]:
                    participants[index].wishes[i] = values[column][i]
                    update_flag = True

            # met à jour la liste des commentaires
            for i in range(0, len(values[column + 1])):
                if participants[index].comments[i] != values[column + 1][i]:
                    participants[index].comments[i] = values[column + 1][i]

            if update_flag:
                new_data_flag = True
                logger.info("mise à jour des cadeaux de " + participants[index].name)

    return new_data_flag


def backup_cadeaux():
    with open(configs.CADEAUX, "wb") as file:
        pickle.dump(participants, file, protocol=pickle.HIGHEST_PROTOCOL)
    logger.info("sauvegarde de l'état de Flantier")


def load_cadeaux():
    with open(configs.CADEAUX, "rb") as file:
        participants = pickle.load(file)

    logger.info("restauration de l'état de Flantier")
    return participants


def init_participants(participants):
    """Initialise la liste des participants avec leur impossibilités et leurs cadeaux.

    retourne l'administrateur
    """
    logger.info("init participants\n")

    # TODO : automatiser à partir d'un fichier de participants
    # liste des personnes
    user1 = Personne(00000000, "User1")
    user2 = Personne(00000000, "User2")
    user3 = Personne(00000000, "User3")

    # on rajoute les tableaux des impossibilités
    user1.impossible = [user2]
    user2.impossible = [user1]
    user3.impossible = []

    logger.info("setup list\n")
    participants.extend([user1, user2, user3])

    logger.info("init cadeaux\n")
    get_cadeaux()

    logger.info("setup administrator\n")
    return configs.administrateur


def tirage():
    """Algorithme de tirage au sort, complète automatique les champs 'dest'."""
    # init
    global imp_total
    imp_total = []

    for qqun in participants:
        qqun.dest = 0

    logger.info("\nC'est parti !!!\n")

    # attribution
    for quelquun in participants:

        # determine la liste des possibles
        possibles = []
        for possibilite in participants:
            if possibilite in imp_total or possibilite in quelquun.impossible:
                continue
            else:
                possibles.append(possibilite)

        # s'il n'y a pas de solution on redémarre
        if len(possibles) == 0:
            logger.info("\nOn recommence !!!\n")
            return -1

        # selectionne qqun
        quelquun.dest = choice(possibles)
        # l'ajoute aux tirés"
        imp_total.append(quelquun.dest)
        # passe au suivant

    # backup_tirage()
    logger.info("\nC'est fini !!!\n")

    return 0


def find_wishes(tg_id, name, with_comments=False, table=False):
    """Trouve et retourne la liste de souhaits avec le nom de la personne."""
    matches = [qqun for qqun in participants if (qqun.name == name)]

    if len(matches) == 0:
        if table:
            return []
        else:
            return "Je n'ai trouvé personne correspondant à ta recherche. N'oublie pas la majuscule."

    if matches[0].tg_id == tg_id:
        if table:
            return []
        else:
            return "Hop hop hop ! Tu ne peux pas consulter ta propre liste de cadeaux, ça gacherait la surprise."

    if not table:
        souhaits = ""
        i = 1
        while matches[0].wishes[i] is not None:

            souhaits += str(i) + " : " + matches[0].wishes[i] + "\n"

            if with_comments and matches[0].comments[i] is not None:
                souhaits += "\n" + matches[0].comments[i] + "\n"

            i += 1

        if len(souhaits) == 0:
            souhaits = name + " n'a rien demandé pour Noël :'("

    else:
        souhaits = []
        i = 1
        while matches[0].wishes[i] is not None:
            souhaits.append(matches[0].wishes[i])
            i += 1
    return souhaits
