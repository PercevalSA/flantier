#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

import time
from logging import getLogger
from multiprocessing import Process
from random import choice

from flantier._users import User, load_users, save_users

logger = getLogger("flantier")


class Roulette:
    """Singleton class to store roulette state."""

    registration: bool = False
    participants: list[User] = []
    # singleton
    __instance = None

    def __new__(cls, *args, **kwargs):
        if Roulette.__instance is None:
            Roulette.__instance = super(Roulette, cls).__new__(cls, *args, **kwargs)
        return Roulette.__instance

    def _is_signed_in(self, tg_id: int) -> bool:
        """Vérifie si l'utilisateur est déjà inscrit."""
        for user in self.participants:
            if user.tg_id == tg_id:
                return True

        return False

    #
    # user management
    #

    def get_user(self, tg_id: int) -> User | None:
        """Récupère un utilisateur par son tg_id"""
        for user in self.participants:
            if user.tg_id == tg_id:
                return user
        return None

    def search_user(self, name: str) -> User | None:
        """Récupère un utilisateur par son nom"""
        for user in self.participants:
            if user.name == name:
                return user
        return None

    def add_user(self, tg_id: int, name: str) -> bool:
        """récupère l'id telegram et ajoute l'utilisateur au fichier.

        Args:
            tg_id (int): telegram id of the new user
            name (str): Name of the user used to filter gifts column in Google Sheets

        Returns:
            bool: true on success, false on error
        """

        if self.get_user(tg_id):
            logger.info("user %s is already known from flantier bot: %d", name, tg_id)
            return False

        logger.info("Adding user %s: %d", name, tg_id)
        self.participants.append(User(tg_id, name))
        logger.info("users: %s", self.participants)
        save_users(self.participants)
        return True

    def remove_user(self, tg_id: int) -> bool:
        """supprime l'utilisateur de la base de données"""
        try:
            self.participants.remove(self.get_user(tg_id))
            save_users(self.participants)
            return True
        except TypeError:
            pass

        return False

    def load_users(self):
        """Charge les participants depuis le fichier de sauvegarde"""
        self.participants = load_users()

    def list_users(self) -> str:
        """Liste les participants inscrits"""
        _users = ""
        for user in self.participants:
            _users += f"{user.name}\n"
        return _users

    #
    # registration management
    #

    def open_registrations(self) -> None:
        """Lance la campagne d'inscription."""
        self.registration = True

    def close_registrations(self) -> None:
        """Termine la campagne d'inscription."""
        self.registration = False

    def _is_registered(self, tg_id: int) -> bool:
        """Vérifie si l'utilisateur participe au tirage au sort."""
        for user in self.participants:
            if user.tg_id == tg_id and user.registered:
                return True

        return False

    def register_user(self, tg_id: int, name: str) -> bool:
        """Inscrit un utilisateur au tirage au sort."""
        logger.info("Inscription de %s: %d", name, tg_id)
        if not self.registration:
            logger.info("Les inscriptions ne sont pas ouvertes")
            return False

        if self._is_registered(tg_id):
            logger.info("%s is already registered: %d", name, tg_id)
            return False

        for user in self.participants:
            if user.tg_id == tg_id:
                user.registered = True
                save_users(self.participants)
                return True

        logger.info("user %s not found: %s", name, tg_id)
        return False

    def unregister_user(self, tg_id: int) -> bool:
        """récupère l'id telegram et supprime le participant"""
        logger.info("Desinscription de %d", tg_id)

        if not self.registration:
            logger.info("Les inscriptions ne sont pas ouvertes")
            return False

        if not self._is_registered(tg_id):
            logger.info("%d is not registered", tg_id)
            return True

        for user in self.participants:
            if user.tg_id == tg_id:
                user.registered = False
                save_users(self.participants)
                return True

        return False

    #
    # roulette management
    #

    def set_spouse(self, tg_id: int, spouse: int) -> bool:
        """Ajoute un conjoint à un participant."""
        for user in self.participants:
            if user.tg_id == tg_id:
                user.spouse = spouse
                save_users(self.participants)
                return True
        return False

    def update_with_last_year_results(self) -> None:
        """update each user last_giftee with the result of last year and reset giftee."""
        for user in self.participants:
            if user.giftee != 0:
                user.last_giftee = user.giftee
                user.giftee = 0
        save_users(self.participants)

    def is_ready(self) -> bool:
        """Vérifie que les conditions sont réunies pour lancer le tirage au sort"""
        return bool(self.participants) and not self.registration

    def _roulette(self) -> bool:
        """Algorithme de tirage au sort, complète automatique les champs 'giftee'."""
        drawn_users = []

        for qqun in self.participants:
            qqun.giftee = 0

        logger.info("\nC'est parti !!!\n")

        # attribution
        for quelquun in self.participants:
            # determine la liste des possibles
            possibles = []
            for possibilite in self.participants:
                if (
                    possibilite.tg_id in drawn_users
                    or possibilite.tg_id == quelquun.spouse
                    or possibilite.tg_id == quelquun.last_giftee
                    or possibilite.tg_id == quelquun.tg_id
                ):
                    continue
                possibles.append(possibilite)

            # s'il n'y a pas de solution on redémarre
            if len(possibles) == 0:
                logger.info("Pas de solution, on recommence le tirage.")
                time.sleep(0.1)
                return False

            giftee = choice(possibles)
            quelquun.giftee = giftee.tg_id
            logger.debug(f"{quelquun.name} offers to {giftee.name}")
            drawn_users.append(quelquun.giftee)

        save_users(self.participants)
        logger.info("the roulette just finished. Results will be send to every user")
        return True

    def roulette(self):
        # tant que le tirage ne fonctionne pas on relance
        while not self._roulette():
            continue
        return True

    def tirage(self):
        roulette_process = Process(target=self.roulette, name="spin_the_wheel")
        roulette_process.start()
        roulette_process.join(timeout=5)
        roulette_process.terminate()
        return roulette_process.exitcode
