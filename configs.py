#!/usr/bin/python3

"""Herr Flantier der Geschenk Manager Configurations."""

# Telegram bot token
TOKEN = ''
# Google API Token
API_key = ''

# file to store users data
PARTICIPANTS = 'participants.txt'
CADEAUX = 'cadeaux.bak'

# Google Sheets Document
spreadsheet_id = ''
sheet_id = ''
nb_cadeaux = 30
data_range = 'A1:AB' + str(nb_cadeaux)
