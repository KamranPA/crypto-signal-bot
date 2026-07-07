# مسیر فایل: notify/telegram_bot.py
"""ارسال سیگنال به تلگرام."""
from __future__ import annotations
import os
import asyncio
from telegram import Bot

from strategy.core import Signal


def format_signal_message(sig: Signal, confidence: float) -> str:
    emoji = "🟦" if sig.direction == "bull" else "⬜"
    direction_fa = "خرید (Bull)" if sig.direction == "bull" else "فروش (Bear)"
    return (
        f"{emoji} <b>سیگنال جدید — {sig.symbol}</b>\n\n"
        f"جهت: {direction_fa}\n"
        f"زمان: {sig.timestamp.strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"اطمینان مدل ML: {confidence:.1%}\n\n"
        f"ورود: <code>{sig.entry:.4f}</code>\n"
        f"حد ضرر: <code>{sig.stop_loss:.4f}</code>\n"
        f"TP1: <code>{sig.tp1:.4f}</code>\n"
        f"TP2: <code>{sig.tp2:.4f}</code>\n"
        f"TP3: <code>{sig.tp3:.4f}</code>"
    )


async def _send(message: str):
    bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
    await bot.send_message(chat_id=os.environ["TELEGRAM_CHAT_ID"], text=message, parse_mode="HTML")


def send_signal(sig: Signal, confidence: float):
    message = format_signal_message(sig, confidence)
    asyncio.run(_send(message))


def send_text(message: str):
    asyncio.run(_send(message))
