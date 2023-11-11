#!/usr/bin/python3
"""Gère les utilisateurs stockés dans le fichier de configuration users.json
"""

import json
from dataclasses import asdict, dataclass, is_dataclass
from logging import getLogger
from pathlib import Path

DEFAULT_USERS_DB = Path.home() / ".cache/flantier/users.json"

logger = getLogger("flantier")


@dataclass
class User:
    """Represents a person registered for secret santa."""

    tg_id: int  # telegram id of the new user
    name: str  # name of the user used to filter gifts column in Google Sheets
    spouse: int = 0  # telegram id of the spouse
    giftee: int = 0  # telegram id of the person to offer a gift
    last_giftee: int = 0  # telegram id of the person who recieved the gift last year
    registered: bool = False  # is the user registered for secret santa

    """
    TODO add
        comments (str): commentaires qui viennent du google doc
        donor (TYPE): liste des personnes qui offrent les cadeaux correspondant
        offer_to (List): liste de [personne, cadeau] que la personne a décidé d'offrir
        wishes (List[str]): cadeaux qui viennent du google doc

        # self.wishes = [None] * configs.nb_cadeaux
        # self.comments = [None] * configs.nb_cadeaux
        # self.donor = [None] * configs.nb_cadeaux
        # self.offer_to = []
    """


class UserJSONEncoder(json.JSONEncoder):
    """JSON encoder for User class."""

    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)


def user_list_to_json(users: list) -> str:
    """Convertit la liste des utilisateurs en JSON."""
    return json.dumps(users, cls=UserJSONEncoder, indent=4)


def json_to_user_list(data: str) -> list:
    """Convertit le JSON en liste d'utilisateurs."""
    return json.loads(data, object_hook=lambda d: User(**d))


def load_users(user_file: Path = DEFAULT_USERS_DB) -> list[User] | None:
    """Charge les utilisateurs enregistrés dans le fichier de sauvegarde."""
    logger.info("Restauration de l'état de Flantier")

    try:
        with open(user_file, "r", encoding="utf-8") as file:
            users = json_to_user_list(file.read())
    except FileNotFoundError:
        logger.warning("users file %s not found, creating one", user_file)
        users = []
        user_file.parent.mkdir(parents=True, exist_ok=True)
        with open(user_file, "w", encoding="utf-8") as file:
            json.dump(users, file, indent=4)

    return users


def save_users(users: list, users_file: Path = DEFAULT_USERS_DB) -> None:
    """Sauvegarde les utilisateurs dans le fichier de sauvegarde."""
    logger.info("Sauvegarde de l'état de Flantier")
    with open(users_file, "w", encoding="utf-8") as file:
        file.write(user_list_to_json(users))
