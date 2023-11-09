#!/usr/bin/python3
"""Gère les utilisateurs stockés dans le fichier de configuration users.json
"""

import json
import logging
from typing import List

from settings import Settings

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

# TODO use a class or dataclass
def person(
    tg_id: int,
    name: str,
    spouse: int = 0,
    giftee: int = 0,
    last_giftee: int = 0,
):
    """Generates a dict representing a person registered for secret santa.

    Args:
        tg_id (int): telegram id of the new user
        name (str): Name of the user used to filter gifts column in Google Sheets
        exclude (List): liste des personnes à qui la personne ne peut pas offrir
        giftee (int): personne à qui offrir

    Returns:
        dict: the person item
    """
    return {
        "tg_id": tg_id,
        "name": name,
        "spouse": spouse,
        "giftee": giftee,
        "last_giftee": last_giftee,
    }


def load_users():
    """Charge les utilisateurs enregistrés dans le fichier de sauvegarde."""
    logger.info("Restauration de l'état de Flantier")

    try:
        with open(Settings().settings.users_file, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = []

    return data


def save_users(users: List):
    """Sauvegarde les utilisateurs dans le fichier de sauvegarde."""
    logger.info("Sauvegarde de l'état de Flantier")
    data = json.dumps(users, indent=4)
    with open(Settings().settings.users_file, "w", encoding="utf-8") as file:
        file.write(data)
