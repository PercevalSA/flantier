"""Herr Flantier der Geschenk Manager."""

from glob import glob
from logging import getLogger
from pathlib import Path
from random import choice

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CallbackContext, CommandHandler, ContextTypes

from flantier._quotes_oss117 import quotes

AUDIO_BASE_FOLDER = Path.home() / ".cache/flantier/"

logger = getLogger("flantier")


async def _send_written_quote(
    chat_id: int,
    context: CallbackContext,
) -> None:
    await context.bot.send_message(chat_id=chat_id, text=choice(quotes))


async def _send_audio_quote(chat_id: int, context: CallbackContext, folder: Path) -> None:
    """Petit Comique."""
    audio_files = glob(f"{folder}/*.mp3")

    if not audio_files:
        logger.error("No audio files found in %s", folder)
        _send_written_quote(chat_id, context)
        return

    audio = folder / Path(choice(audio_files))
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_AUDIO)
    with open(audio, "rb") as audio_file:
        await context.bot.send_audio(
            chat_id=chat_id, audio=audio_file, disable_notification=True
        )


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Petit Comique."""
    _send_written_quote(update.message.chat_id, context)


async def quote_oss1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Petit Comique."""
    _send_audio_quote(
        update.message.chat_id,
        context,
        AUDIO_BASE_FOLDER / "phrases-cultes-de-oss-117-le-caire-nid-d-espions",
    )


async def quote_oss2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Petit Comique."""
    _send_audio_quote(
        update.message.chat_id,
        context,
        AUDIO_BASE_FOLDER / "phrases-cultes-de-oss-117-rio-ne-repond-plus",
    )


def register_flantier_commands(application: Application) -> None:
    """Register Flantier commands: specific to Noël Flantier for fun only"""
    application.add_handler(CommandHandler("bonjour", hello))
    application.add_handler(CommandHandler("larmina", quote_oss1))
    application.add_handler(CommandHandler("dolores", quote_oss2))
