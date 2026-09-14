"""Subtext CLI — concall diff over BSE filings."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Windows consoles default to cp1252, which raises on the arrows, dashes and
# quotes this output is built from. Force UTF-8 before anything prints.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from . import batch as batch_mod, bse, claims as claims_mod, providers, render, universe  # noqa: E402
from .diffengine import compare  # noqa: E402
from .transcript import ANALYST, JOURNALIST, MANAGEMENT, parse as parse_pdf  # noqa: E402

NO_ATTRIBUTION = "\n".join([
    "This filing has no speaker markers — the transcript is continuous prose,",
    "  so management and analyst remarks cannot be separated. Extracting from it",
    "  would mix analyst questions into what we report as management commentary,",
    "  so Subtext declines rather than publish something it cannot stand behind.",
    "  Try another quarter with --index, or another ticker.",
])


def _resolve(ticker: str):
    scrip = bse.resolve_ticker(ticker)
    print(f"  {scrip.ticker} -> BSE {scrip.code}  {scrip.name}  {scrip.isin}",
          file=sys.stderr)
    return scrip


def _load_transcript(scrip, index: int, months: int):
    found = bse.find_transcripts(scrip.code, months_back=months)
    if not found:
        raise SystemExit(f"No transcripts found for {scrip.ticker}.")
    if index >= len(found):
        raise SystemExit(f"Index {index} out of range — only {len(found)} found.")
    filing = found[index]
    print(f"  [{index}] {filing.date}  downloading...", file=sys.stderr)
    return filing, parse_pdf(bse.fetch_transcript_pdf(filing))


def cmd_transcripts(args) -> int:
    scrip = _resolve(args.ticker)
    found = bse.find_transcripts(scrip.code, months_back=args.months)
    if not found:
        print(f"No earnings-call transcripts found for {scrip.ticker} "
              f"in the last {args.months} months.")
        return 1
    print(f"\n  {len(found)} earnings-call transcript(s):\n")
    for i, f in enumerate(found):
        print(f"   [{i}] {f.date}  {f.headline[:64]}")
    return 0


def cmd_parse(args) -> int:
    scrip = _resolve(args.ticker)
    filing, tr = _load_transcript(scrip, args.index, args.months)
    print(f"\n  {scrip.name} — {filing.date}")
    print(f"  {filing.headline[:64]}\n")

    if not tr.attributed:
        print(f"  {NO_ATTRIBUTION}")
        return 1

    stats = tr.stats()
    print(f"  turns      {stats['turns']}")
    print(f"  speakers   {stats['speakers']}")
    for role in (MANAGEMENT, ANALYST, JOURNALIST):
        turns = tr.by_role(role)
        if turns:
            print(f"  {role:<10} {len(turns):>3} turns, "
                  f"{sum(t.words for t in turns):>6} words")
    print("\n  speakers:")
    for name, role in sorted(tr.roles.items(), key=lambda x: (x[1], x[0])):
        print(f"    {role:<11} {name}")
    return 0


def cmd_extract(args) -> int:
    scrip = _resolve(args.ticker)
    filing, tr = _load_transcript(scrip, args.index, args.months)
    if not tr.attributed:
        raise SystemExit(f"\n  {NO_ATTRIBUTION}")

    ext = claims_mod.extract(tr, ticker=scrip.ticker, period_hint=filing.date,
                             refresh=args.refresh)
    bad = claims_mod.verify_quotes(ext, tr)
    print(f"\n  {scrip.ticker} — {ext.period_label}  (tone {ext.tone_score}/10)")
    print(f"  {ext.tone_rationale}\n")
    for c in ext.claims:
        flag = "   [unverified]" if c in bad else ""
        print(f"   • {c.topic.value:<20} [{c.stance.value}]{flag}")
        print(f"     {c.statement}")
        if c.figures:
            print(f"     figures: {', '.join(c.figures)}")
    if bad:
        print(render.unverified_warning(bad))
    return 0


def cmd_diff(args) -> int:
    scrip = _resolve(args.ticker)
    found = bse.find_transcripts(scrip.code, months_back=args.months)
    if len(found) < 2:
        raise SystemExit(
            f"Need two transcripts to diff; found {len(found)} for {scrip.ticker}. "
            f"Try a wider --months window.")

    new_f, old_f = found[args.index], found[args.index + 1]
    print(f"  new: {new_f.date}   old: {old_f.date}", file=sys.stderr)

    new_tr = parse_pdf(bse.fetch_transcript_pdf(new_f))
    old_tr = parse_pdf(bse.fetch_transcript_pdf(old_f))
    for label, tr in (("newer", new_tr), ("older", old_tr)):
        if not tr.attributed:
            raise SystemExit(f"\n  {label} filing ({tr.source.name}): {NO_ATTRIBUTION}")

    new_ex = claims_mod.extract(new_tr, ticker=scrip.ticker,
                                period_hint=new_f.date, refresh=args.refresh)
    old_ex = claims_mod.extract(old_tr, ticker=scrip.ticker,
                                period_hint=old_f.date, refresh=args.refresh)

    # Never diff on a claim we cannot trace back to the transcript.
    bad = claims_mod.verify_quotes(new_ex, new_tr) + claims_mod.verify_quotes(old_ex, old_tr)
    if bad:
        bad_ids = {id(c) for c in bad}
        new_ex.claims = [c for c in new_ex.claims if id(c) not in bad_ids]
        old_ex.claims = [c for c in old_ex.claims if id(c) not in bad_ids]

    d = compare(old_ex, new_ex, ticker=scrip.ticker)
    print()
    print(render.diff(d, company=scrip.name))
    if bad:
        print(render.unverified_warning(bad))

    if args.telegram:
        from . import telegram as tg
        chat_id = args.chat_id or os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id:
            print("\n  --telegram needs a chat id: pass --chat-id or set "
                  "TELEGRAM_CHAT_ID in .env.\n  Run `python -m subtext telegram` "
                  "to find yours.", file=sys.stderr)
            return 1
        try:
            n = tg.send_diff(chat_id, d, company=scrip.name)
            print(f"\n  sent to Telegram ({n} message{'s' if n > 1 else ''})")
        except tg.TelegramError as e:
            print(f"\n  Telegram: {e}", file=sys.stderr)
            return 1
    return 0


def cmd_telegram(args) -> int:
    from . import telegram as tg
    try:
        me = tg.whoami()
    except tg.TelegramError as e:
        print(f"\n  {e}")
        return 1
    print(f"\n  bot ok: @{me.get('username')}  ({me.get('first_name')})")
    chats = tg.recent_chat_ids()
    if not chats:
        print("\n  No chats yet. Open Telegram, send your bot any message,")
        print("  then run this again to see your chat id.")
        return 0
    print("\n  chats that have messaged this bot:")
    for c in chats:
        print(f"    {c['chat_id']}   {c['type']:<10} {c['name']}")
    print("\n  Put the id you want in .env as TELEGRAM_CHAT_ID.")
    return 0


def cmd_providers(args) -> int:
    print("\n  LLM providers (first one with a key set is used):\n")
    active = None
    try:
        active = providers.detect()
    except providers.ProviderError:
        pass
    for p in providers.PROVIDERS:
        mark = "->" if active and p.name == active.name else "  "
        state = "key set" if p.key else "not set"
        print(f"  {mark} {p.name:<12} {p.env_key:<22} {state:<9} {p.note}")
    if not active:
        print("\n  None configured. Put one key in .env - see the list above.")
        return 1
    print(f"\n  active: {active.name}  model: {providers.model_for(active)}")
    if args.models:
        try:
            names = providers.available_models(active)
        except providers.ProviderError as e:
            print(f"\n  could not list models: {e}")
            return 1
        print(f"\n  {len(names)} model(s) this key can use:")
        for n in names[:40]:
            print(f"    {n}")
    return 0


def cmd_batch(args) -> int:
    tickers = universe.nifty(args.universe)
    if args.limit:
        tickers = tickers[:args.limit]
    print(f"  Nifty {args.universe}: {len(tickers)} tickers, "
          f"searching {args.months} months back\n", file=sys.stderr)

    rep = batch_mod.run(tickers, months=args.months)
    out = Path(args.out)
    rep.save(out)
    print(batch_mod.format_report(rep))
    print(f"  full report -> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="subtext", description="What they're really saying.")
    p.add_argument("--months", type=int, default=18,
                   help="How far back to search BSE (default 18).")
    sub = p.add_subparsers(dest="cmd", required=True)

    for name, fn, helptext in [
        ("transcripts", cmd_transcripts, "List earnings-call transcripts on BSE"),
        ("parse", cmd_parse, "Parse one transcript and show speaker attribution"),
        ("extract", cmd_extract, "Extract structured management claims (needs API key)"),
        ("diff", cmd_diff, "Diff the two most recent quarters (needs API key)"),
    ]:
        sp = sub.add_parser(name, help=helptext)
        sp.add_argument("ticker", help="NSE ticker, e.g. INFY")
        sp.set_defaults(func=fn)
        if name != "transcripts":
            sp.add_argument("--index", type=int, default=0,
                            help="0 = most recent transcript.")
        if name in ("extract", "diff"):
            sp.add_argument("--refresh", action="store_true",
                            help="Ignore cached extraction and re-run the model.")
        if name == "diff":
            sp.add_argument("--telegram", action="store_true",
                            help="Also deliver the diff to Telegram.")
            sp.add_argument("--chat-id", default="",
                            help="Telegram chat id (else TELEGRAM_CHAT_ID).")

    pp = sub.add_parser("providers", help="Show which LLM provider is configured")
    pp.add_argument("--models", action="store_true", help="Also list usable models.")
    pp.set_defaults(func=cmd_providers)

    tp = sub.add_parser("telegram", help="Check the bot token / find your chat id")
    tp.set_defaults(func=cmd_telegram)

    bp = sub.add_parser("batch", help="Coverage run across an index (no API key)")
    bp.add_argument("--universe", type=int, default=100, choices=universe.SIZES)
    bp.add_argument("--limit", type=int, default=0, help="Only the first N tickers.")
    bp.add_argument("--out", default="data/coverage.json")
    bp.set_defaults(func=cmd_batch)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except (LookupError, RuntimeError, ValueError) as e:
        print(f"\n  error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
