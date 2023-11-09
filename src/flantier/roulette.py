#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

import logging
from random import choice
from typing import List

import users

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

    def _does_participate(self, tg_id: int):
        for id, user in enumerate(self.participants):
            if user["tg_id"] == tg_id:
                return id, user
        return None, None

    def add_user(self, tg_id: int, name: str) -> int:
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

        tgid, _ = self._does_participate(tg_id)
        if tgid:
            logger.info("%s est déjà enregistré: %d", name, tg_id)
            return -2

        logger.info("Inscription de %s: %d", name, tg_id)
        self.participants.append(users.person(tg_id, name))
        users.save_users(self.participants)
        return 0

    def remove_user(self, tg_id: int) -> bool:
        """récupère l'id telegram et supprime le participant"""
        if self.inscriptions_open:
            tgid, _ = self._does_participate(tg_id)
            try:
                self.participants.pop(tgid)
                users.save_users(self.participants)
                return True

            except TypeError:
                pass
        return False

    def load_users(self):
        """Charge les participants depuis le fichier de sauvegarde"""
        self.participants = users.load_users()

    def list_users(self) -> str:
        """Liste les participants inscrits"""
        _users = ""
        for user in self.participants:
            _users += f"{user['name']}\n"
        return _users

    def get_user(self, tg_id: int) -> dict:
        """Récupère un utilisateur par son tg_id"""
        for user in self.participants:
            if user["tg_id"] == tg_id:
                return user
        return False

    def search_user(self, name: str):
        """Récupère un utilisateur par son nom"""
        for user in self.participants:
            if user["name"] == name:
                return user
        return None

    def exclude(self, tg_id: int, exclude: int):
        """Ajoute un utilisateur à la liste des exclus d'un autre"""
        for user in self.participants:
            if user["tg_id"] == user:
                user["exclude"].append(exclude)
                return True
                # FIXME uncomment
                # users.save_users(self.participants)
        return False

    def is_ready(self):
        """Vérifie que les conditions sont réunies pour lancer le tirage au sort"""
        return bool(len(self.participants)) and not self.inscriptions_open

    def tirage(self) -> bool:
        """Algorithme de tirage au sort, complète automatique les champs 'dest'."""
        drawn_users = []

        for qqun in self.participants:
            qqun["dest"] = 0

        logger.info("\nC'est parti !!!\n")

        # attribution
        for quelquun in self.participants:
            # determine la liste des possibles
            possibles = []
            for possibilite in self.participants:
                if (
                    possibilite["tg_id"] in drawn_users
                    or possibilite["tg_id"] in quelquun["exclude"]
                    or possibilite["tg_id"] == quelquun["tg_id"]
                ):
                    continue
                possibles.append(possibilite)

            # s'il n'y a pas de solution on redémarre
            if len(possibles) == 0:
                logger.info("Pas de solution, on recommence le tirage.")
                return False

            dest = choice(possibles)
            quelquun["dest"] = dest["tg_id"]
            print(f"{quelquun['name']} offre à {dest['name']}")
            drawn_users.append(quelquun["dest"])

        print(self.participants)
        users.save_users(self.participants)
        logger.info("Tirage terminé, les résulats sont tombés.")

        return True
