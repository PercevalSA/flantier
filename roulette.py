#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

from random import choice

# Global variables
participants = []
imp_total = []
inscriptions = True

logger = logging.getLogger("flantier")


class Roulette():

    # singleton
    __instance = None

    def __new__(cls,*args, **kwargs):
        if Roulette.__instance is None :
            Roulette.__instance = super(Roulette, cls).__new__(cls, *args, **kwargs)
        return Roulette.__instance


    def init_participants(participants):
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


    def tirage():
        """Algorithme de tirage au sort, complète automatique les champs 'dest'."""
        # init
        global imp_total
        imp_total = []

        for qqun in participants:
            qqun.dest = 0

        logger.info("\nC'est parti !!!\n")

        # attribution
        for quelquun in participants:

            # determine la liste des possibles
            possibles = []
            for possibilite in participants:
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
