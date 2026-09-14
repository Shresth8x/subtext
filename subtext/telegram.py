"""Telegram delivery.

Raw Bot API over HTTPS — no extra dependency for what is two endpoints.

Telegram caps a message at 4096 characters and a concall diff can exceed that,
so messages are split on section boundaries rather than mid-quote.
"""
from __future__ import annotations

import os
import re

import requests

from .diffengine import Diff

API = "https://api.telegram.org/bot{token}/{method}"
LIMIT = 3900          # headroom under Telegram's 4096 for the code fence
DISCLAIMER = "Research Only — Not Investment Advice"


class TelegramError(RuntimeError):
    pass


def _token() -> str:
    tok = os.getenv("TELEGRAM_BOT_TOKEN")
    if not tok:
        raise TelegramError(
            "TELEGRAM_BOT_TOKEN is not set. Create a bot with @BotFather on "
            "Telegram, then put the token in .env.")
    return tok


def _esc(s: str) -> str:
    """Escape for Telegram MarkdownV2."""
    return re.sub(r"([_*\[\]()~`>#+\-=|{}.!\\])", r"\\\1", s)


def send(chat_id: str, text: str, *, markdown: bool = True) -> dict:
    payload = {"chat_id": chat_id, "text": text,
               "disable_web_page_preview": True}
    if markdown:
        payload["parse_mode"] = "MarkdownV2"
    r = requests.post(API.format(token=_token(), method="sendMessage"),
                      json=payload, timeout=30)
    body = r.json()
    if not body.get("ok"):
        raise TelegramError(f"Telegram rejected the message: {body.get('description')}")
    return body


def _chunks(text: str, limit: int = LIMIT) -> list[str]:
    """Split on blank lines so a quote never straddles two messages."""
    out, cur = [], ""
    for block in text.split("\n\n"):
        candidate = f"{cur}\n\n{block}" if cur else block
        if len(candidate) <= limit:
            cur = candidate
            continue
        if cur:
            out.append(cur)
        # A single oversized block still has to go somewhere.
        while len(block) > limit:
            out.append(block[:limit])
            block = block[limit:]
        cur = block
    if cur:
        out.append(cur)
    return out


def format_diff(d: Diff, *, company: str = "") -> str:
    """Telegram-flavoured rendering. Deliberately terser than the terminal view."""
    title = company or d.ticker
    lines = [f"🔎 *CONCALL DIFF — {_esc(title)}*",
             _esc(f"{d.new_label} vs {d.old_label}"), "", _esc(d.headline()), ""]

    soft = [s for s in d.shifts if s.delta < 0]
    hard = [s for s in d.shifts if s.delta > 0]

    if soft:
        lines.append("*😟 LANGUAGE SOFTENED*")
        for s in soft:
            lines.append(f"*{_esc(s.topic.value.upper())}*  "
                         f"{_esc(s.old.stance.value)} → {_esc(s.new.stance.value)} "
                         f"\\({s.delta:+d}\\)")
            lines.append(f"_{_esc(d.old_label)}:_ \"{_esc(s.old.quote)}\"")
            lines.append(f"_{_esc(d.new_label)}:_ \"{_esc(s.new.quote)}\"")
            lines.append("")

    if hard:
        lines.append("*💪 LANGUAGE FIRMED UP*")
        for s in hard:
            lines.append(f"*{_esc(s.topic.value.upper())}*  "
                         f"{_esc(s.old.stance.value)} → {_esc(s.new.stance.value)}")
            lines.append(f"\"{_esc(s.new.quote)}\"")
            lines.append("")

    if d.new_topics:
        lines.append("*🆕 RAISED FOR THE FIRST TIME*")
        for c in d.new_topics:
            lines.append(f"*{_esc(c.topic.value.upper())}* \\[{_esc(c.stance.value)}\\]")
            lines.append(f"\"{_esc(c.quote)}\"")
            lines.append("")

    if d.dropped_topics:
        lines.append("*🔇 STOPPED DISCUSSING*")
        for c in d.dropped_topics:
            lines.append(f"*{_esc(c.topic.value.upper())}* — "
                         f"{_esc(f'raised in {d.old_label}, absent in {d.new_label}')}")
            lines.append(f"\"{_esc(c.quote)}\"")
            lines.append("")

    arrow = "↓" if d.tone_delta < 0 else ("↑" if d.tone_delta > 0 else "→")
    lines.append(f"*TONE* {d.tone_old}/10 → {d.tone_new}/10 {arrow} "
                 f"\\({d.tone_delta:+d}\\)")
    lines.append("")
    lines.append(f"_{_esc(DISCLAIMER)}_")
    return "\n".join(lines)


def send_diff(chat_id: str, d: Diff, *, company: str = "") -> int:
    parts = _chunks(format_diff(d, company=company))
    for part in parts:
        send(chat_id, part)
    return len(parts)


def whoami() -> dict:
    """Verify the token works. `getMe` is the cheapest possible check."""
    r = requests.get(API.format(token=_token(), method="getMe"), timeout=20)
    body = r.json()
    if not body.get("ok"):
        raise TelegramError(f"Token rejected: {body.get('description')}")
    return body["result"]


def recent_chat_ids() -> list[dict]:
    """Chat IDs that have messaged the bot — how you find your own chat_id.

    Send the bot any message first, then call this.
    """
    r = requests.get(API.format(token=_token(), method="getUpdates"), timeout=20)
    body = r.json()
    if not body.get("ok"):
        raise TelegramError(f"getUpdates failed: {body.get('description')}")
    seen, out = set(), []
    for upd in body.get("result", []):
        chat = (upd.get("message") or upd.get("channel_post") or {}).get("chat")
        if chat and chat["id"] not in seen:
            seen.add(chat["id"])
            out.append({"chat_id": chat["id"],
                        "name": chat.get("first_name") or chat.get("title") or "",
                        "type": chat.get("type")})
    return out
