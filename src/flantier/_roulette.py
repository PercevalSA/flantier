"""Herr Flantier der Geschenk Manager."""

import sys
from logging import getLogger
from multiprocessing import Process
from random import choice
from time import sleep
from typing import List

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

    def register_user(self, tg_id: int) -> bool:
        """Inscrit un utilisateur au tirage au sort."""
        user_manager = UserManager()
        name = user_manager.get_user(tg_id).name

        logger.info("Inscription de %s: %d", name, tg_id)
        if not self.registration:
            logger.info("Les inscriptions ne sont pas ouvertes")
            return False

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

    def _roulette(self, participants: List[User]) -> bool:
        """Algorithme de tirage au sort, complète automatique les champs 'giftee'."""
        drawn_users = []

        for one in participants:
            one.giftee = 0

        logger.info("starting the roulette, spinning the wheel of fortuuuune")
        logger.debug(participants)

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
                logger.info("No solution found, let's draw again.")
                return False

            giftee = choice(possibilities)
            one.giftee = giftee.tg_id
            logger.debug("%s offers to %s", one.name, giftee.name)
            drawn_users.append(one.giftee)

        logger.info("the roulette just finished.")
        return True

    def roulette_process(self):
        """execute le tirage au sort."""
        # tant que le tirage ne fonctionne pas on relance
        user_manager = UserManager()
        participants = [user for user in user_manager.users if user.registered]
        logger.debug("participants: %s", participants)

        if len(participants) < 2:
            logger.warning("not enough registered users: canceling draw")
            sys.exit(1)

        while not self._roulette(participants):
            sleep(0.1)
            continue

        user_manager.save_users()

    def tirage(self) -> int:
        """Lance le tirage au sort dans un processus séparé."""
        roulette_process = Process(target=self.roulette_process, name="spin_the_wheel")
        roulette_process.start()
        roulette_process.join(timeout=5)
        roulette_process.terminate()  # exitcode = None
        if roulette_process.exitcode is None:
            logger.warning("roulette process timed out")
            return 1
        logger.info("roulette process terminated with code %d", roulette_process.exitcode)
        # we need to reload data from the file as draw has been done in a separate process
        UserManager().load_users()
        return roulette_process.exitcode
