"""Terminal rendering of a concall diff."""
from __future__ import annotations

import textwrap

from .diffengine import Diff

RULE = "─" * 68
DISCLAIMER = "Research Only — Not Investment Advice"


def _wrap(text: str, indent: str = "     ") -> str:
    return textwrap.fill(text, width=68, initial_indent=indent,
                         subsequent_indent=indent)


def _quote(text: str, indent: str = "     ") -> str:
    body = textwrap.fill(f'"{text}"', width=66,
                         initial_indent=indent + "│ ", subsequent_indent=indent + "│ ")
    return body


def diff(d: Diff, *, company: str = "") -> str:
    out: list[str] = []
    title = company or d.ticker
    out.append(RULE)
    out.append(f"  CONCALL DIFF — {title}")
    out.append(f"  {d.new_label} vs {d.old_label}")
    out.append(RULE)
    out.append("")
    out.append(_wrap(d.headline(), indent="  "))
    out.append("")

    softened = [s for s in d.shifts if s.delta < 0]
    hardened = [s for s in d.shifts if s.delta > 0]

    if softened:
        out.append("  LANGUAGE SOFTENED")
        for s in softened:
            out.append(f"   • {s.topic.value.replace('_', ' ').upper()}"
                       f"   {s.old.stance.value} → {s.new.stance.value}  ({s.delta:+d})")
            out.append(f"     {d.old_label}:")
            out.append(_quote(s.old.quote))
            out.append(f"     {d.new_label}:")
            out.append(_quote(s.new.quote))
            out.append("")

    if hardened:
        out.append("  LANGUAGE FIRMED UP")
        for s in hardened:
            out.append(f"   • {s.topic.value.replace('_', ' ').upper()}"
                       f"   {s.old.stance.value} → {s.new.stance.value}  ({s.delta:+d})")
            out.append(_quote(s.new.quote))
            out.append("")

    if d.new_topics:
        out.append("  RAISED FOR THE FIRST TIME")
        for c in d.new_topics:
            out.append(f"   • {c.topic.value.replace('_', ' ').upper()}  [{c.stance.value}]")
            out.append(_wrap(c.statement))
            out.append(_quote(c.quote))
            out.append("")

    if d.dropped_topics:
        out.append("  STOPPED DISCUSSING")
        for c in d.dropped_topics:
            out.append(f"   • {c.topic.value.replace('_', ' ').upper()}"
                       f"  — raised in {d.old_label}, absent in {d.new_label}")
            out.append(_quote(c.quote))
            out.append("")

    if d.steady:
        unchanged = ", ".join(s.topic.value.replace("_", " ") for s in d.steady)
        out.append(f"  UNCHANGED: {unchanged}")
        out.append("")

    arrow = "↓" if d.tone_delta < 0 else ("↑" if d.tone_delta > 0 else "→")
    out.append(f"  TONE  {d.tone_old}/10 → {d.tone_new}/10  {arrow} ({d.tone_delta:+d})")
    out.append("")
    out.append(RULE)
    out.append(f"  {DISCLAIMER}")
    out.append(RULE)
    return "\n".join(out)


def unverified_warning(bad: list) -> str:
    if not bad:
        return ""
    lines = ["", "  ⚠ QUOTE VERIFICATION FAILED",
             f"  {len(bad)} claim(s) cite a quote not found verbatim in the transcript.",
             "  These are suppressed from the diff above.", ""]
    for c in bad:
        lines.append(f"   • {c.topic.value}: \"{c.quote[:70]}...\"")
    return "\n".join(lines)
