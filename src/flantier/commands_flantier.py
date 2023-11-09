#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

import logging
import os
from pathlib import Path
from random import choice

import configs
import keyboards
import noel_flantier
import santa
from roulette import Roulette
from telegram import (
    ChatAction,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

def hello(update: Update, context: CallbackContext):
    """Petit Comique."""
    context.bot.send_message(
        chat_id=update.message.chat_id, text=choice(noel_flantier.quotes)
    )


def send_audio_quote(chat_id: int, context: CallbackContext, folder: Path):
    """Petit Comique."""
    audio_files = os.listdir(folder)
    audio = folder / Path(choice(audio_files))

    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_AUDIO)
    # pylint: disable=R1732
    context.bot.send_audio(
        chat_id=chat_id, audio=open(audio, "rb"), disable_notification=True
    )


def quote_oss1(update: Update, context: CallbackContext):
    """Petit Comique."""
    send_audio_quote(update.message.chat_id, context, Path("audio/oss1"))


def quote_oss2(update: Update, context: CallbackContext):
    """Petit Comique."""
    send_audio_quote(update.message.chat_id, context, Path("audio/oss2"))
