"""Herr Flantier der Geschenk Manager."""

from glob import glob
from logging import getLogger
from pathlib import Path
from random import choice

from telegram import (
    ChatAction,
    Update,
)
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Dispatcher,
)

from flantier._quotes_oss117 import quotes

AUDIO_BASE_FOLDER = Path.home() / ".cache/flantier/"

logger = getLogger("flantier")


def _send_written_quote(
    chat_id: int,
    context: CallbackContext,
) -> None:
    context.bot.send_message(chat_id=chat_id, text=choice(quotes))


def _send_audio_quote(chat_id: int, context: CallbackContext, folder: Path) -> None:
    """Petit Comique."""
    audio_files = glob(f"{folder}/*.mp3")

    if not audio_files:
        logger.error("No audio files found in %s", folder)
        _send_written_quote(chat_id, context)
        return

    audio = folder / Path(choice(audio_files))
    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_AUDIO)
    with open(audio, "rb") as audio_file:
        context.bot.send_audio(
            chat_id=chat_id, audio=audio_file, disable_notification=True
        )


def hello(update: Update, context: CallbackContext) -> None:
    """Petit Comique."""
    _send_written_quote(update.message.chat_id, context)


def quote_oss1(update: Update, context: CallbackContext) -> None:
    """Petit Comique."""
    _send_audio_quote(
        update.message.chat_id,
        context,
        AUDIO_BASE_FOLDER / "phrases-cultes-de-oss-117-le-caire-nid-d-espions",
    )


def quote_oss2(update: Update, context: CallbackContext) -> None:
    """Petit Comique."""
    _send_audio_quote(
        update.message.chat_id,
        context,
        AUDIO_BASE_FOLDER / "phrases-cultes-de-oss-117-rio-ne-repond-plus",
    )


def register_flantier_commands(dispatcher: Dispatcher) -> None:
    """Register Flantier commands: specific to the Flantier bot for fun only"""
    dispatcher.add_handler(CommandHandler("bonjour", hello))
    dispatcher.add_handler(CommandHandler("larmina", quote_oss1))
    dispatcher.add_handler(CommandHandler("dolores", quote_oss2))
