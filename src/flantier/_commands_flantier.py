#!/usr/bin/python3
"""Herr Flantier der Geschenk Manager."""

import logging
from glob import glob
from pathlib import Path
from random import choice

from telegram import (
    ChatAction,
    Update,
)
from telegram.ext import (
    CallbackContext,
)

from flantier._quotes_oss117 import quotes

logger = logging.getLogger("flantier")


def hello(update: Update, context: CallbackContext):
    """Petit Comique."""
    context.bot.send_message(chat_id=update.message.chat_id, text=choice(quotes))


def send_audio_quote(chat_id: int, context: CallbackContext, folder: Path):
    """Petit Comique."""
    audio_files = glob(f"{folder}/*.mp3")
    audio = folder / Path(choice(audio_files))

    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_AUDIO)
    # pylint: disable=R1732
    context.bot.send_audio(
        chat_id=chat_id, audio=open(audio, "rb"), disable_notification=True
    )


def quote_oss1(update: Update, context: CallbackContext):
    """Petit Comique."""
    send_audio_quote(
        update.message.chat_id,
        context,
        Path("phrases-cultes-de-oss-117-le-caire-nid-d-espions"),
    )


def quote_oss2(update: Update, context: CallbackContext):
    """Petit Comique."""
    send_audio_quote(
        update.message.chat_id,
        context,
        Path("phrases-cultes-de-oss-117-rio-ne-repond-plus"),
    )
