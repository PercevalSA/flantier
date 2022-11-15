#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager.
"""

# import json
import configs

class Personne:
    """classe représentant les personnes inscrites au secret santa.

    Attributes:
        comments (TYPE): commentaires qui viennent du google doc
        dest (TYPE): personne à qui offrir
        donor (TYPE): liste des personnes qui offrent les cadeaux correspondant
        impossible (list): liste des personnes à qui la personne ne peut pas offrir
        name (TYPE): nom de la personne utiliser pour trouver la colonne dans google doc
        offer_to (list): liste de [personne, cadeau] que la personne a décidé d'offrir
        tg_id (TYPE): telegram id de la personne
        wishes (TYPE): cadeaux qui viennent du google doc
    """

    def __init__(self, tg_id: int, name: str):
        """Personne class init function.

        Args:
            tg_id (int): telegram id of the new user
            name (str): Name of the user used to filter gifts column in Google Sheets
        """
        self.tg_id = tg_id
        self.name = name
        self.impossible = []
        self.dest = None
        self.wishes = [None] * configs.nb_cadeaux
        self.comments = [None] * configs.nb_cadeaux
        self.donor = [None] * configs.nb_cadeaux
        self.offer_to = []


def get_users_from_file(file: Path):
    with open(configs.USERS_FILE, 'r') as file:
        users = file.read()

    print(users)

def register_user_to_file(user: Personne, file: Path):

def backup_cadeaux():
    with open(configs.CADEAUX, "wb") as file:
        pickle.dump(participants, file, protocol=pickle.HIGHEST_PROTOCOL)
    logger.info("sauvegarde de l'état de Flantier")


def load_cadeaux():
    with open(configs.CADEAUX, "rb") as file:
        participants = pickle.load(file)

    logger.info("restauration de l'état de Flantier")
    return participants