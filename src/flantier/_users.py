"""Gère les utilisateurs stockés dans le fichier de configuration users.json
We are using dataclass to represent Users and wishes (gifts)
source https://www.delftstack.com/howto/python/dataclass-to-json-in-python/
"""

import json
from dataclasses import asdict, dataclass, field, is_dataclass
from logging import getLogger
from pathlib import Path
from random import randint
from typing import Any, List, Optional

DEFAULT_USERS_DB = Path.home() / ".cache/flantier/users.json"

logger = getLogger("flantier")


@dataclass
class Wish:
    """Represents a wish from a user."""

    wish: str  # cadeaux qui viennent du google doc
    comment: str  # commentaires qui viennent du google doc
    giver: int = 0  # la personne qui offre ce cadeau

    def __dict__(self):  # type: ignore
        return asdict(self)

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)


@dataclass
class User:
    """Represents a person registered for secret santa."""

    tg_id: int  # telegram id of the new user; positive integer; if negative integer the user has no telegram account
    name: str  # name of the user used to filter gifts column in Google Sheets
    spouse: int = 0  # telegram id of the spouse
    giftee: int = 0  # telegram id of the person to offer a gift
    last_giftee: int = 0  # telegram id of the person who recieved the gift last year
    registered: bool = False  # is the user registered for secret santa
    # list of wishes as Wish objects
    wishes: List[Wish] = field(default_factory=list)


class UserJSONEncoder(json.JSONEncoder):
    """JSON encoder for User and Wish classes."""

    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)


# pylint: disable=C0103,R1710
def UserJSONDecoder(json_dict: dict) -> Any:
    """JSON decoder function for User and Wish classes."""
    if "tg_id" in json_dict:
        return User(**json_dict)
    if "wish" in json_dict:
        return Wish(**json_dict)


def user_list_to_json(users: list) -> str:
    """Convert"""
    return json.dumps(users, cls=UserJSONEncoder, indent=4, ensure_ascii=False)


def json_to_user_list(data: str) -> list:
    """Convertit le JSON en liste d'utilisateurs."""
    # return json.loads(data, object_hook=lambda d: User(**d))
    return json.loads(data, object_hook=UserJSONDecoder)


class UserManager:
    """Singleton class to store roulette state."""

    users: List[User] = []
    # singleton
    __instance = None

    def __new__(cls, *args, **kwargs):
        if UserManager.__instance is None:
            UserManager.__instance = super(
                UserManager, cls).__new__(cls, *args, **kwargs)
        return UserManager.__instance

    #
    # user management
    #

    def get_user(self, tg_id: int) -> Optional[User]:
        """Récupère un utilisateur par son tg_id. Si registered est True,
        ne renvoie que les utilisateurs inscrits pour le tirage au sort.
        """
        for user in self.users:
            if user.tg_id == tg_id:
                return user

        return None

    def search_user(self, name: str) -> Optional[User]:
        """Récupère un utilisateur par son nom"""
        for user in self.users:
            if user.name == name:
                return user

        return None

    def is_registered(self, tg_id: int) -> bool:
        """Renvoie True si l'utilisateur est inscrit au tirage au sort."""
        user = self.get_user(tg_id)
        if user:
            return user.registered
        return False

    def add_user(self, name: str, tg_id: Optional[int] = None) -> bool:
        """récupère l'id telegram et ajoute l'utilisateur au fichier. 
        Si aucun id n'est fourni, un id négatif est généré pour indiquer que l'utilisateur 
        n'a pas de compte telegram.    

        Args:
            tg_id (Optional[int]): telegram id of the new user
            name (str): Name of the user used to filter gifts column in Google Sheets

        Returns:
            bool: true on success, false on error
        """

        # the user has no telegram account so we generate a random negative id
        if tg_id is None:
            while True:
                tg_id = randint(-99999999, -10000000)
                if not self.get_user(tg_id):
                    break

        if self.get_user(tg_id):
            logger.info(
                "user %s is already known from flantier bot: %d", name, tg_id)
            return False

        user = self.search_user(name)
        if user:
            logger.info("updating user %s: %d", name, tg_id)
            user.tg_id = tg_id
        else:
            logger.info("adding user %s: %d", name, tg_id)
            self.users.append(User(tg_id, name))

        logger.debug("users: %s", self.users)
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
        for i, u in enumerate(self.users):
            # some users have tg_id = 0
            if u.tg_id == user.tg_id and u.name == user.name:
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

    def get_user_constraints(self, user_id: int) -> str:
        """Get user constraints as str. Get spouse and last giftee names if any."""
        user = self.get_user(user_id)
        logger.debug("searching for %s constraints", user)

        if user.spouse == 0 and user.last_giftee == 0:
            text = f"{user.name} peut offrir à tout le monde"
        if user.spouse == 0 or user.last_giftee == 0:
            try:
                constraint = self.get_user(user.spouse)
            except RuntimeError as e:
                logger.error(e)
            try:
                constraint = self.get_user(user.last_giftee)
            except RuntimeError as e:
                logger.error(e)

            text = f"{user.name} ne peut pas offrir à {constraint.name}"
        else:
            text = (
                f"{user.name} ne peut pas offrir à"
                f" {self.get_user(user.spouse).name} et à"
                f" {self.get_user(user.last_giftee).name}"
            )

        return text

    # manage users file
    def load_users(self, user_file: Path = DEFAULT_USERS_DB) -> None:
        """Charge les utilisateurs enregistrés dans le fichier de sauvegarde."""
        logger.debug("Restauration de l'état de Flantier depuis %s", user_file)

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
        logger.debug("Sauvegarde de l'état de Flantier: %s", users_file)
        with open(
            users_file,
            "w",
            encoding="utf-8",
        ) as file:
            file.write(user_list_to_json(self.users))
