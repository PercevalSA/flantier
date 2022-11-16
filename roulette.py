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
    participants: List

    # singleton
    __instance = None

    def __new__(cls, *args, **kwargs):
        if Roulette.__instance is None:
            Roulette.__instance = super(Roulette, cls).__new__(cls, *args, **kwargs)
        return Roulette.__instance


    def register_user(self, tg_id: int, name: str) -> bool:
        """récupère l'id telegram et ajoute le participant au fichier.

        Args:
            tg_id (int): telegram id of the new user
            name (str): Name of the user used to filter gifts column in Google Sheets

        Returns:
            bool: whether the user is registered or not
        """
        if not self.inscriptions_open:
            return False

        for person in self.participants:
            if tg_id == person.tg_id:
                return False

        logger.info(f"Inscription de {name}: {tg_id}")
        self.participants.append(json.dumps(users.Personne(tg_id, name).__dict__))
        users.save_users(self.participants)
        return True


    def load_users(self):
        self.participants = users.load_users()


    def init_participants(self, participants):
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


    def is_ready(self):
        return bool(len(self.participants)) and not self.inscriptions_open


    def tirage(self):
        """Algorithme de tirage au sort, complète automatique les champs 'dest'."""
        imp_total = []

        for qqun in self.participants:
            qqun.dest = 0

        logger.info("\nC'est parti !!!\n")

        # attribution
        for quelquun in self.participants:

            # determine la liste des possibles
            possibles = []
            for possibilite in self.participants:
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
