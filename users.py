#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager.
"""

import json
import configs
from typing import List
import logging

logger = logging.getLogger("flantier")

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
        # self.wishes = [None] * configs.nb_cadeaux
        # self.comments = [None] * configs.nb_cadeaux
        # self.donor = [None] * configs.nb_cadeaux
        # self.offer_to = []

    # def toJSON(self):
    #     return json.dumps(self, default=lambda o: o.__dict__, 
    #         sort_keys=True, indent=4)

def load_users():
    logger.info("Restauration de l'état de Flantier")
    with open(configs.USERS_FILE, 'r') as file:
        data = json.load(file)

    print(data)

    return data


def save_users(users: List):
    logger.info("Sauvegarde de l'état de Flantier")
    data = json.dumps(users, indent=4)
    with open(configs.USERS_FILE, "w") as file:
        file.write(data)
