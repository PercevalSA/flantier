#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

import users
from random import choice
import logging
import configs
from typing import List
import json

logger = logging.getLogger("flantier")


class Roulette:
    inscriptions_open: bool
    participants: List[dict]

    # singleton
    __instance = None

    def __new__(cls, *args, **kwargs):
        if Roulette.__instance is None:
            Roulette.__instance = super(Roulette, cls).__new__(cls, *args, **kwargs)
        return Roulette.__instance


    def register_user(self, tg_id: int, name: str) -> int:
        """récupère l'id telegram et ajoute le participant au fichier.

        Args:
            tg_id (int): telegram id of the new user
            name (str): Name of the user used to filter gifts column in Google Sheets

        Returns:
            int:
                0 : user is correclty registered
                -1: inscription are not open yet
                -2: user is already registered
        """
        if not self.inscriptions_open:
            return -1

        for person in self.participants:
            if tg_id == person['tg_id']:
                logger.info(f"{name} est déjà enregistré: {tg_id}")
                return -2

        logger.info(f"Inscription de {name}: {tg_id}")
        self.participants.append(users.person(tg_id, name))
        users.save_users(self.participants)
        return 0


    def load_users(self):
        self.participants = users.load_users()


    def list_users(self) -> str:
        users = ""
        for user in self.participants:
            users += f"{user['name']}\n"
        return users


    def init_participants(self, participants: List[dict]):
        """Initialise la liste des participants avec leur impossibilités et leurs cadeaux."""
        logger.info("Initialisation des participant.e.s\n")

        # TODO do interactive selection for administator
        # on rajoute les tableaux des impossibilités
        user1['exclude'] = [user2['tg_id']]
        user2['exclude'] = [user1['tg_id']]
        user3['exclude'] = []

        # logger.info("init cadeaux\n")
        # get_cadeaux()


    def is_ready(self):
        return bool(len(self.participants)) and not self.inscriptions_open


    def tirage(self) -> bool:
        """Algorithme de tirage au sort, complète automatique les champs 'dest'."""
        drawn_users = []

        for qqun in self.participants:
            qqun['dest'] = 0

        logger.info("\nC'est parti !!!\n")

        # attribution
        for quelquun in self.participants:

            # determine la liste des possibles
            possibles = []
            for possibilite in self.participants:
                if possibilite['tg_id'] in drawn_users or possibilite['tg_id'] in quelquun['exclude'] or possibilite['tg_id'] == quelquun['tg_id']:
                    continue
                else:
                    possibles.append(possibilite)

            # s'il n'y a pas de solution on redémarre
            if len(possibles) == 0:
                logger.info("Pas de solution, on recommence le tirage.")
                return False

            dest = choice(possibles)
            quelquun['dest'] = dest['tg_id']
            print(f"{quelquun['name']} offre à {dest['name']}")
            drawn_users.append(quelquun['dest'])

        print(self.participants)
        users.save_users(self.participants)
        logger.info("Tirage terminé, les résulats sont tombés.")

        return True
