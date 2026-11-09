"""IA DEL REY — Agedsocial promo bot (polling version)."""

import asyncio
import json
import logging
import os
from datetime import timedelta
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import Forbidden, TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("agedsocial-bot")

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBSITE = "https://agedsocial.com"
SUBSCRIBERS_FILE = Path("subscribers.json")

WELCOME_DELAY = 5      # wait before the "no blockage" message
SECOND_DELAY = 2       # wait before deleting the welcome message
DELETE_DELAY = 3       # wait before the promo message
PROMO_SECONDS = 60     # length of the 1-minute promo
REMINDER_EVERY = timedelta(hours=5)

# --------------------------------------------------------------------------- #
# Texts (HTML so we don't have to escape MarkdownV2 punctuation)
# --------------------------------------------------------------------------- #
WELCOME = (
    "Are you a working boy or a hustler looking for a confirmed US FB account "
    "with pages or an IG account?\n\n"
    f'Agedsocial is the right option for you 👉 <a href="{WEBSITE}">agedsocial.com</a>'
)

BLOCKAGE = "🔥 <b>FB and IG with NO CHANCE OF BLOCKAGE</b>"

PROMO = (
    "⏰ <b>1 Minute Promo</b>\n\n"
    "Visit the website in the next minute and get an account at an "
    "<b>80% discount</b>.\n\n"
    f'👉 <a href="{WEBSITE}">agedsocial.com</a>'
)

PROMO_OVER = (
    "⌛ <b>The 1-minute window is closed…</b>\n\n"
    "But you still have a chance — you can still get an account at a discount.\n\n"
    f'👉 <a href="{WEBSITE}">agedsocial.com</a>'
)

REMINDER = (
    "🔔 <b>Agedsocial update</b>\n\n"
    "Fresh US FB accounts (with pages) and IG accounts are available right now — "
    "no chance of blockage.\n\n"
    f'👉 <a href="{WEBSITE}">agedsocial.com</a>'
)


def website_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🌐 Get my account — agedsocial.com", url=WEBSITE)]]
    )


# --------------------------------------------------------------------------- #
# State (subscribers survive a restart via subscribers.json)
# --------------------------------------------------------------------------- #
def _load_subscribers() -> set[int]:
    try:
        return {int(x) for x in json.loads(SUBSCRIBERS_FILE.read_text())}
    except Exception:
        return set()


subscribers: set[int] = _load_subscribers()
flows: dict[int, asyncio.Task] = {}


def _save_subscribers() -> None:
    try:
        SUBSCRIBERS_FILE.write_text(json.dumps(sorted(subscribers)))
    except Exception:
        logger.warning("could not persist subscribers", exc_info=True)


# --------------------------------------------------------------------------- #
# The timed promo sequence
# --------------------------------------------------------------------------- #
async def _promo_flow(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot = context.bot
    try:
        # t = 0s — welcome
        welcome = await bot.send_message(chat_id, WELCOME, parse_mode="HTML")

        # t = 5s — "no chance of blockage"
        await asyncio.sleep(WELCOME_DELAY)
        await bot.send_message(chat_id, BLOCKAGE, parse_mode="HTML")

        # t = 7s — delete the welcome message
        await asyncio.sleep(SECOND_DELAY)
        try:
            await bot.delete_message(chat_id, welcome.message_id)
        except TelegramError:
            logger.info("welcome message for %s could not be deleted", chat_id)

        # t = 10s — promo with button
        await asyncio.sleep(DELETE_DELAY)
        await bot.send_message(
            chat_id, PROMO, parse_mode="HTML", reply_markup=website_button()
        )

        # t = 70s — countdown over
        await asyncio.sleep(PROMO_SECONDS)
        await bot.send_message(
            chat_id, PROMO_OVER, parse_mode="HTML", reply_markup=website_button()
        )

    except asyncio.CancelledError:
        logger.info("promo flow for %s cancelled (user restarted)", chat_id)
        raise
    except Exception:
        logger.exception("promo flow failed for chat %s", chat_id)


# --------------------------------------------------------------------------- #
# Handlers
# --------------------------------------------------------------------------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    if chat_id not in subscribers:
        subscribers.add(chat_id)
        _save_subscribers()

    # If they hit /start again mid-flow, kill the old sequence first.
    previous = flows.get(chat_id)
    if previous and not previous.done():
        previous.cancel()

    task = asyncio.create_task(_promo_flow(chat_id, context))

    def _cleanup(t: asyncio.Task, cid: int = chat_id) -> None:
        if not t.cancelled():
            t.exception()  # mark as retrieved
        if flows.get(cid) is t:
            flows.pop(cid, None)

    task.add_done_callback(_cleanup)
    flows[chat_id] = task


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    subscribers.discard(chat_id)
    _save_subscribers()

    task = flows.pop(chat_id, None)
    if task and not task.done():
        task.cancel()

    await update.message.reply_text(
        "Okay, reminders stopped. Send /start anytime to begin again."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "/start — see the Agedsocial promo\n"
        "/stop — stop the 5-hour reminders\n\n"
        f"Website: {WEBSITE}"
    )


# --------------------------------------------------------------------------- #
# 5-hour broadcast
# --------------------------------------------------------------------------- #
async def send_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not subscribers:
        return

    logger.info("sending 5h reminder to %d subscriber(s)", len(subscribers))
    for chat_id in list(subscribers):
        try:
            await context.bot.send_message(
                chat_id, REMINDER, parse_mode="HTML", reply_markup=website_button()
            )
        except Forbidden:
            # user blocked the bot / deleted the chat
            subscribers.discard(chat_id)
            _save_subscribers()
        except TelegramError:
            logger.warning("reminder failed for %s", chat_id, exc_info=True)
        await asyncio.sleep(0.05)  # stay well under the 30 msg/s limit


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")

    app = Application.builder().token(BOT_TOKEN).build()

    if app.job_queue is None:
        raise SystemExit(
            "JobQueue is unavailable — install python-telegram-bot[job-queue]"
        )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_cmd))

    app.job_queue.run_repeating(
        send_reminders,
        interval=REMINDER_EVERY,
        first=REMINDER_EVERY,
        name="agedsocial-5h-reminder",
    )

    logger.info("IA DEL REY (Agedsocial promo bot) is running…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
