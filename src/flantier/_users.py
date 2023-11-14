#!/usr/bin/python3
"""Gère les utilisateurs stockés dans le fichier de configuration users.json
"""

import json
from dataclasses import asdict, dataclass, field, is_dataclass
from logging import getLogger
from pathlib import Path

DEFAULT_USERS_DB = Path.home() / ".cache/flantier/users.json"

logger = getLogger("flantier")


# @dataclass
# class Wish:
#     wish: str  # cadeaux qui viennent du google doc
#     comment: str  # commentaires qui viennent du google doc
#     giver: str  # la personne qui offre ce cadeau


@dataclass
class User:
    """Represents a person registered for secret santa."""

    tg_id: int  # telegram id of the new user
    name: str  # name of the user used to filter gifts column in Google Sheets
    spouse: int = 0  # telegram id of the spouse
    giftee: int = 0  # telegram id of the person to offer a gift
    last_giftee: int = 0  # telegram id of the person who recieved the gift last year
    registered: bool = False  # is the user registered for secret santa
    # TODO use Wish dataclass instead of dict
    wishes: list = field(default_factory=list)  # list of wishes as tuple (wish, comment)


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


class UserManager:
    """Singleton class to store roulette state."""

    users: list[User] = []
    # singleton
    __instance = None

    def __new__(cls, *args, **kwargs):
        if UserManager.__instance is None:
            UserManager.__instance = super(UserManager, cls).__new__(cls, *args, **kwargs)
        return UserManager.__instance

    #
    # user management
    #

    def get_user(self, tg_id: int) -> User:
        """Récupère un utilisateur par son tg_id. Si registered est True,
        ne renvoie que les utilisateurs inscrits pour le tirage au sort.
        """
        for user in self.users:
            if user.tg_id == tg_id:
                return user

        return None  # type: ignore

    def search_user(self, name: str) -> User:
        """Récupère un utilisateur par son nom"""
        for user in self.users:
            if user.name == name:
                return user

        return None  # type: ignore

    def is_registered(self, tg_id: int) -> bool:
        """Renvoie True si l'utilisateur est inscrit au tirage au sort."""
        return self.get_user(tg_id).registered

    def add_user(self, tg_id: int, name: str) -> bool:
        """récupère l'id telegram et ajoute l'utilisateur au fichier.

        Args:
            tg_id (int): telegram id of the new user
            name (str): Name of the user used to filter gifts column in Google Sheets

        Returns:
            bool: true on success, false on error
        """

        if self.get_user(tg_id) and tg_id != 0:
            logger.info("user %s is already known from flantier bot: %d", name, tg_id)
            return False

        logger.info("Adding user %s: %d", name, tg_id)
        self.users.append(User(tg_id, name))
        logger.info("users: %s", self.users)
        self.save_users()
        return True

    def remove_user(self, tg_id: int) -> bool:
        """supprime l'utilisateur de la base de données"""
        try:
            self.users.remove(self.get_user(tg_id))  # type: ignore
            self.save_users()
            return True
        except TypeError:
            pass

        return False

    def update_user(self, user: User) -> bool:
        """Met à jour l'utilisateur dans la base de données"""
        for i, _user in enumerate(self.users):
            if _user.tg_id == user.tg_id:
                self.users[i] = user
                self.save_users()
                return True
        return False

    def list_users(self) -> str:
        """Liste les users inscrits"""
        _users = ""
        for user in self.users:
            _users += f"{user.name}\n"
        return _users

    def set_spouse(self, tg_id: int, spouse: int) -> bool:
        """Ajoute un conjoint à un participant."""
        for user in self.users:
            if user.tg_id == tg_id:
                user.spouse = spouse
                self.save_users()
                return True
        return False

    def update_with_last_year_results(self) -> None:
        """update each user last_giftee with the result of last year and reset giftee."""
        for user in self.users:
            if user.giftee != 0:
                user.last_giftee = user.giftee
                user.giftee = 0
        self.save_users()

    # manage users file
    def load_users(self, user_file: Path = DEFAULT_USERS_DB) -> None:
        """Charge les utilisateurs enregistrés dans le fichier de sauvegarde."""
        logger.info("Restauration de l'état de Flantier")

        try:
            with open(user_file, "r", encoding="utf-8") as file:
                self.users = json_to_user_list(file.read())
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            logger.warning("users file %s not found, creating one", user_file)
            user_file.parent.mkdir(parents=True, exist_ok=True)
            with open(user_file, "w", encoding="utf-8") as file:
                json.dump(self.users, file, indent=4)

    def save_users(self, users_file: Path = DEFAULT_USERS_DB) -> None:
        """Sauvegarde les utilisateurs dans le fichier de sauvegarde."""
        logger.info("Sauvegarde de l'état de Flantier")
        with open(users_file, "w", encoding="utf-8") as file:
            file.write(user_list_to_json(self.users))
