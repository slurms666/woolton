import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Set

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from message_formatter import format_weather_message
from weather_api import get_weather_data

SUBSCRIBERS_FILE = Path(__file__).with_name("subscribers.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def load_subscribers() -> Set[int]:
    if not SUBSCRIBERS_FILE.exists():
        return set()
    try:
        data = json.loads(SUBSCRIBERS_FILE.read_text(encoding="utf-8"))
        return {int(x) for x in data.get("subscribers", [])}
    except Exception:
        logging.exception("Failed reading subscribers.json; starting empty")
        return set()


def save_subscribers(subscribers: Set[int]) -> None:
    payload = {"subscribers": sorted(subscribers)}
    SUBSCRIBERS_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def add_subscriber(user_id: int) -> bool:
    subscribers = load_subscribers()
    before = len(subscribers)
    subscribers.add(user_id)
    save_subscribers(subscribers)
    return len(subscribers) > before


def remove_subscriber(user_id: int) -> bool:
    subscribers = load_subscribers()
    if user_id not in subscribers:
        return False
    subscribers.remove(user_id)
    save_subscribers(subscribers)
    return True


async def _build_weather_message() -> str:
    weather_data = get_weather_data()
    return format_weather_message(weather_data)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    added = add_subscriber(user_id)

    if added:
        text = "✅ Subscribed. You will receive daily weather at 07:00 (Europe/London)."
    else:
        text = "✅ You are already subscribed to daily weather updates."

    await update.message.reply_text(text)

    # send weather immediately
    try:
        message = await _build_weather_message()
        await update.message.reply_text(message)
    except Exception as exc:
        logging.exception("Weather fetch failed")
        await update.message.reply_text(f"⚠️ Could not fetch weather data: {exc}")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    removed = remove_subscriber(user_id)

    if removed:
        text = "🛑 Unsubscribed. You will no longer receive daily weather updates."
    else:
        text = "You were not subscribed."

    await update.message.reply_text(text)


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        message = await _build_weather_message()
    except Exception as exc:
        logging.exception("/weather failed")
        await update.message.reply_text(f"⚠️ Could not fetch weather data: {exc}")
        return

    await update.message.reply_text(message)


async def send_daily_weather(token: str) -> None:
    app = Application.builder().token(token).build()
    subscribers = load_subscribers()

    if not subscribers:
        logging.info("No subscribers; skipping daily send")
        return

    try:
        message = await _build_weather_message()
    except Exception:
        logging.exception("Failed to build weather message")
        return

    sent = 0

    for user_id in subscribers:
        try:
            await app.bot.send_message(chat_id=user_id, text=message)
            sent += 1
        except Exception:
            logging.exception("Failed to send message to %s", user_id)

    logging.info("Daily weather send complete: %s/%s", sent, len(subscribers))


async def process_pending_updates(token: str) -> None:
    """Process queued commands for scheduled workflow runs."""
    app = Application.builder().token(token).build()

    updates = await app.bot.get_updates(timeout=10, allowed_updates=["message"])

    if not updates:
        logging.info("No pending updates")
        return

    for upd in updates:
        msg = upd.message

        if not msg or not msg.text:
            continue

        text = msg.text.strip().lower()
        user_id = msg.from_user.id

        if text.startswith("/start"):
            add_subscriber(user_id)

            await app.bot.send_message(
                chat_id=user_id,
                text="✅ Subscribed. You will receive daily weather at 07:00 (Europe/London).",
            )

            # send weather immediately
            try:
                message = await _build_weather_message()
                await app.bot.send_message(chat_id=user_id, text=message)
            except Exception as exc:
                logging.exception("Weather fetch failed")
                await app.bot.send_message(
                    chat_id=user_id,
                    text=f"⚠️ Could not fetch weather data: {exc}",
                )

        elif text.startswith("/stop"):
            removed = remove_subscriber(user_id)

            await app.bot.send_message(
                chat_id=user_id,
                text="🛑 Unsubscribed." if removed else "You were not subscribed.",
            )

        elif text.startswith("/weather"):
            try:
                message = await _build_weather_message()
            except Exception as exc:
                message = f"⚠️ Could not fetch weather data: {exc}"

            await app.bot.send_message(chat_id=user_id, text=message)

        # mark update processed
        await app.bot.get_updates(offset=upd.update_id + 1)


async def run_polling_bot(token: str) -> None:
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("weather", weather_command))

    logging.info("Starting bot polling...")
    await app.run_polling()


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN environment variable")

    run_mode = os.getenv("RUN_MODE", "daily").strip().lower()

    logging.info("RUN_MODE=%s", run_mode)

    if run_mode == "bot":
        asyncio.run(run_polling_bot(token))
    else:
        asyncio.run(process_pending_updates(token))
        asyncio.run(send_daily_weather(token))


if __name__ == "__main__":
    main()
