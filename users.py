#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager.
"""

import json
import configs
from typing import List
import logging

logger = logging.getLogger("flantier")

"""
TODO
Attributes:
    comments (str): commentaires qui viennent du google doc
    donor (TYPE): liste des personnes qui offrent les cadeaux correspondant
    offer_to (List): liste de [personne, cadeau] que la personne a décidé d'offrir
    wishes (List[str]): cadeaux qui viennent du google doc

    # self.wishes = [None] * configs.nb_cadeaux
    # self.comments = [None] * configs.nb_cadeaux
    # self.donor = [None] * configs.nb_cadeaux
    # self.offer_to = []
"""

def person(tg_id: int, name: str, exclude: List = [], dest: int = None):
    """Generates a dict representing a person registered for secret santa.

    Args:
        tg_id (int): telegram id of the new user
        name (str): Name of the user used to filter gifts column in Google Sheets
        exclude (int): liste des personnes à qui la personne ne peut pas offrir
        dest (int): personne à qui offrir

    Returns:
        dict: the person item
    """
    person = {
        'tg_id': tg_id,
        'name': name,
        'exclude': exclude,
        'dest': dest,
    }
    return person


def load_users():
    logger.info("Restauration de l'état de Flantier")

    try:
        with open(configs.USERS_FILE, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = []

    return data


def save_users(users: List):
    logger.info("Sauvegarde de l'état de Flantier")
    data = json.dumps(users, indent=4)
    with open(configs.USERS_FILE, "w") as file:
        file.write(data)
