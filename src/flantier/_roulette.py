#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

from logging import getLogger
from multiprocessing import Process
from random import choice
from time import sleep

from flantier._users import User, UserManager

logger = getLogger("flantier")


class Roulette:
    """Singleton class to store roulette state."""

    registration: bool = False
    # singleton
    __instance = None

    def __new__(cls, *args, **kwargs):
        if Roulette.__instance is None:
            Roulette.__instance = super(Roulette, cls).__new__(cls, *args, **kwargs)
        return Roulette.__instance

    #
    # registration management
    #

    def open_registrations(self) -> None:
        """Lance la campagne d'inscription."""
        self.registration = True

    def close_registrations(self) -> None:
        """Termine la campagne d'inscription."""
        self.registration = False

    def register_user(self, tg_id: int, name: str) -> bool:
        """Inscrit un utilisateur au tirage au sort."""
        logger.info("Inscription de %s: %d", name, tg_id)
        if not self.registration:
            logger.info("Les inscriptions ne sont pas ouvertes")
            return False

        user_manager = UserManager()

        if user_manager.is_registered(tg_id):
            logger.info("%s is already registered: %d", name, tg_id)
            return False

        for user in user_manager.users:
            if user.tg_id == tg_id:
                user.registered = True
                user_manager.save_users()
                return True

        logger.info("user %s not found: %s", name, tg_id)
        return False

    def unregister_user(self, tg_id: int) -> bool:
        """récupère l'id telegram et supprime le participant"""
        logger.info("Desinscription de %d", tg_id)

        if not self.registration:
            logger.info("Les inscriptions ne sont pas ouvertes")
            return False

        user_manager = UserManager()

        if not user_manager.is_registered(tg_id):
            logger.info("%d is not registered", tg_id)
            return True

        for user in user_manager.users:
            if user.tg_id == tg_id:
                user.registered = False
                user_manager.save_users()
                return True

        return False

    #
    # roulette management
    #

    def is_ready(self) -> bool:
        """Vérifie que les conditions sont réunies pour lancer le tirage au sort"""
        return bool(UserManager().users) and not self.registration

    def _roulette(self, participants: list[User]) -> bool:
        """Algorithme de tirage au sort, complète automatique les champs 'giftee'."""
        drawn_users = []

        for one in participants:
            one.giftee = 0

        logger.info("\nC'est parti !!!\n")

        logger.info(participants)
        # attribution
        for one in participants:
            # build the possibles giftees list
            possibilities = []
            for candidate in participants:
                if (
                    candidate.tg_id in drawn_users
                    or candidate.tg_id == one.spouse
                    or candidate.tg_id == one.last_giftee
                    or candidate.tg_id == one.tg_id
                ):
                    continue
                possibilities.append(candidate)

            # no solutions
            if len(possibilities) == 0:
                logger.info("Pas de solution, on recommence le tirage.")
                return False

            giftee = choice(possibilities)
            one.giftee = giftee.tg_id
            logger.debug("%s offers to %s", one.name, giftee.name)
            drawn_users.append(one.giftee)

        logger.info("the roulette just finished. Results will be send to every user")
        return True

    def roulette(self):
        """Lance le tirage au sort."""
        # tant que le tirage ne fonctionne pas on relance
        user_manager = UserManager()
        participants = [user for user in user_manager.users if user.registered]

        logger.info(participants)
        if len(participants) < 2:
            logger.warning("not enough registered users: canceling tirage")
            return False

        while not self._roulette(participants):
            sleep(0.1)
            continue

        user_manager.save_users()
        return True

    def tirage(self):
        """Lance le tirage au sort dans un processus séparé."""
        roulette_process = Process(target=self.roulette, name="spin_the_wheel")
        roulette_process.start()
        roulette_process.join(timeout=5)
        roulette_process.terminate()
        logger.info("roulette process terminated: %d", roulette_process.exitcode)
        return roulette_process.exitcode
