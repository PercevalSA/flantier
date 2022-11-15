#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

import configs
from apiclient.discovery import build
import logging
import pickle

logger = logging.getLogger("flantier")

# TODO use singleton to store state


def get_cadeaux():

    service = build("sheets", "v4", credentials=None, developerKey=configs.API_key)
    request = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=configs.spreadsheet_id,
            range=configs.data_range,
            majorDimension="COLUMNS",
        )
    )
    spreadsheet = request.execute()

    values = spreadsheet.get("values")
    # data_json = json.dumps(values, indent=4, ensure_ascii=False)
    new_data_flag = False

    for column in range(0, len(values), 2):
        name = values[column][0]
        index = next(
            (i for i, qqun in enumerate(participants) if qqun.name == name), -1
        )

        # mise à jour de la liste de cadeaux si les élements sont différents
        if index != -1:
            update_flag = False
            # met à jour la liste des cadeaux
            for i in range(0, len(values[column])):
                if participants[index].wishes[i] != values[column][i]:
                    participants[index].wishes[i] = values[column][i]
                    update_flag = True

            # met à jour la liste des commentaires
            for i in range(0, len(values[column + 1])):
                if participants[index].comments[i] != values[column + 1][i]:
                    participants[index].comments[i] = values[column + 1][i]

            if update_flag:
                new_data_flag = True
                logger.info("mise à jour des cadeaux de " + participants[index].name)

    return new_data_flag


def backup_cadeaux():
    with open(configs.CADEAUX, "wb") as file:
        pickle.dump(participants, file, protocol=pickle.HIGHEST_PROTOCOL)
    logger.info("sauvegarde de l'état de Flantier")


def load_cadeaux():
    with open(configs.CADEAUX, "rb") as file:
        participants = pickle.load(file)

    logger.info("restauration de l'état de Flantier")
    return participants


def register_user(tg_id: int, name: str) -> bool:
    u"""récupère l'id telegram et ajoute le participant au fichier.

    Args:
        tg_id (int): telegram id of the new user
        name (str): Name of the user used to filter gifts column in Google Sheets

    Returns:
        bool: whether the user is registered or not
    """
    if inscriptions:
        with open(configs.USERS_FILE, "a") as file:
            file.write(
                f"{tg_id}:{name}\n"
            )
        logger.info(
            f"Inscription de : {name} : {tg_id}"
        )
    return inscriptions


def find_wishes(tg_id, name, with_comments=False, table=False):
    """Trouve et retourne la liste de souhaits avec le nom de la personne."""
    matches = [qqun for qqun in participants if (qqun.name == name)]

    if len(matches) == 0:
        if table:
            return []
        else:
            return "Je n'ai trouvé personne correspondant à ta recherche. N'oublie pas la majuscule."

    if matches[0].tg_id == tg_id:
        if table:
            return []
        else:
            return "Hop hop hop ! Tu ne peux pas consulter ta propre liste de cadeaux, ça gacherait la surprise."

    if not table:
        souhaits = ""
        i = 1
        while matches[0].wishes[i] is not None:

            souhaits += str(i) + " : " + matches[0].wishes[i] + "\n"

            if with_comments and matches[0].comments[i] is not None:
                souhaits += "\n" + matches[0].comments[i] + "\n"

            i += 1

        if len(souhaits) == 0:
            souhaits = name + " n'a rien demandé pour Noël :'("

    else:
        souhaits = []
        i = 1
        while matches[0].wishes[i] is not None:
            souhaits.append(matches[0].wishes[i])
            i += 1
    return souhaits
