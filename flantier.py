#!/usr/bin/env python3
#  -*- coding: utf-8 -*-
#
# Herr Flantier der Geschenk Manager

from apiclient.discovery import build
import json

# Telegram bot token
TOKEN = ''
# Google API Token
API_key = ''

# file to store users data
PARTICIPANTS = "participants.txt"
CADEAUX = "cadeaux.txt"

# Google Sheets Document
spreadsheet_id = ''
sheet_id = ''
data_range = ''


class Personne:
    def __init__(self, tg_id, name):
        self.tg_id = tg_id
        self.name = name
        # liste des personnes à qui la personne ne peut pas offrir
        self.impossible = []
        # personne à qui offrir
        self.dest = None

        # cadeaux qui viennent du google doc
        self.wishes = None
        self.comments = None

# Global variables
imp_total = []
data_json = None
participants = []
administrateur = None
inscriptions = False


def init_cadeaux():

    global data_json

    print("init cadeaux\n")

    # init
    service = build('sheets', 'v4', credentials=None, developerKey=API_key)
    request = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=data_range, majorDimension='COLUMNS')
    spreadsheet = request.execute()
    values = spreadsheet.get('values')

    data_json = json.dumps(values, indent=4, ensure_ascii=False)
    return values


def backup_cadeaux():
    with open(CADEAUX, 'w+') as file:
        file.write(data_json)


def load_cadeaux():
    global data_json
    with open(CADEAUX, 'r') as file:
        data = file.read()
    data_json = json.loads(data)


def init_participants(administrateur, participants):

    print("init participants\n")

    # liste des personnes
    user1 = Personne(00000000, "User1")
    user2 = Personne(00000000, "User2")
    user3 = Personne(00000000, "User3")

    # on rajoute les tableaux des impossibilités
    user1.impossible = [user2]
    user2.impossible = [user1]
    user3.impossible = []

    values = init_cadeaux()

    user1.wishes = values[0]
    user1.comments = values[1]
    user2.wishes = values[2]
    user2.comments = values[3]
    user3.wishes = values[4]
    user3.comments = values[5]

    # on compose le tout
    print("setup administrator\n")
    administrateur = user1

    print("composition\n")
    participants.extend([user1, user2, user3])


citations = ["Tu n'es pas seulement un lâche, tu es un traitre, comme ta petite taille le laissait deviner.",
             "23 à 0 ! C'est la piquette Jack ! Tu sais pas jouer Jack ! T'es mauvais !",
             "C'est marrant, c'est toujours les nazis qui ont le mauvais rôle. Nous sommes en 1955, herr Bramard, on peut avoir une deuxième chance, merci.",
             "Alors étranger, on part sans dire au revoir ?",
             "Je n'ai jamais pu refuser quoi que ce soit à une brune aux yeux marrons\n- Et si j'étais blonde aux yeux bleus ?\n- Cela ne changerait rien vous êtes mon type de femme Larmina...\n- Tiens donc... Et si j'étais naine et myope ?\n- Et bien, je ne vous laisserais pas conduire. Ça n'a pas de sens...",
             "- Vous voulez terminer comme ces poulets ? Vous voulez mourir Bramard ? Décapité, vidé, plumé, c'est ça qu'vous voulez ?\n- Si c'est pour garder mes poules, oui !",
             "En tout cas, on peut dire que le soviet éponge...",
             "J'aime quand on m'enduit d'huile...",
             "J'aime me beurrer la biscotte !",
             "J'aime me battre.",
             "Comment est votre blanquette ?",
             "- Nous avons besoin de vous sur place. Un Expert. Un spécialiste du monde Arabo-Musulman.\n- Arabo... ?",
             "- J'ai été réveillé par un homme qui hurlait à la mort du haut de cette tour ! J'ai dû le faire taire.\n- Quoi ?! Vous avez fait taire le muezzin !! \n- Ah ! C'était donc ça tout ce tintouin.",
             "C'est notre RAIS a nous, René COTI ! Un grand homme, il marquera l'histoire, il aime les cochinchinois, les malgaches, les sénégalais, les marocains... c'est donc ton ami.",
             "- Mais ce sera surtout l'occasion de rencontrer le gratin Cairote.\n- Et non pas le gratin de pommes de terre ! ... Nan, parce que ça ressemble à carotte, Cairote. Le... le légume, puisque vous avez dit gratin... Gratin de pommes de terre... C'est, c'est une astuce...",
             "Il s'agirait de grandir hein, il s'agirait de grandir...",
             "- Rhha... les sales rouges !\n- Bah, non, les sales jaunes !",
             "C'est l'inexpugnable arrogance de votre beauté qui m'asperge.",
             "- Son fils Heinrich est ici à Rio, je crois me souvenir qu'il habite dans la favela. Aux dernières nouvelles il vit dans un groupe hippy.\n- Dans un quoi ?\n- Groupe hippy !\n- Oh grand dieu, vivre dans l'urine c'est affligeant. Mais ou va le monde ?",
             "Non mais oh ! Comment tu parles de ton père ! Qui c'est qui t'as nourri ? Moi jamais je parlerais de mon père comme ça, jamais ! Moi mon père il était charron ; et j' peux t' dire qu'ça filait doux ! Ça, la mère de la Bath elle mouffetait pas ! Et les enfants non plus d'ailleurs.",
             "Changer le monde, changer le monde vous êtes bien sympathiques mais faudrait déjà vous levez le matin.",
             "C'est le vrai monde dehors et le vrai monde il va chez le coiffeur.",
             "Enfin ça fait un peu Jacques a dit a dit pas de charcuterie !",
             "L'humour juif c'est quand ce n'est pas drôle et que ça ne parle pas de saucisses.",
             "Ah, sacré Hubert, toujours le mot pour rire, ah ah !",
             "Habile !",
             "- L'idée est que nous travaillons ensemble d'égal à égal\n- On en reparlera quand il faudra porter quelque chose de lourd.",
             "- Vous confondez les Juifs et les Musulmans !\n- Vous jouez sur les mots, Dolorès.",
             "Une dictature c'est quand les gens sont communistes, déjà, ils ont froid, avec des chapeaux gris, et des chaussures à fermeture éclaire.",
             "Vous avez bien une amicale des anciens nazis ? un club ? une association peut-être ?",
             "- Tous les allemands ne sont pas Nazis !\n- Oui, j'ai déjà entendu cette théorie quelque part.",
             "Écoutez mon ptit, là j'viens d'tuer un croco'. Alors si vous voulez qu'on travaille d'égal à égal, faudrait vous y mettre.",
             "- C'est vrai que pour rencontrer monsieur Lee, vaut mieux avoir une bonne couverture !\n- Parce que sinon on serait dans de beaux draps !"]
