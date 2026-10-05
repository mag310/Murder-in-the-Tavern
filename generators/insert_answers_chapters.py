#!/usr/bin/env python3
"""Insert the generated `::: answers` blocks into the chapter md files at the
right anchor (before the '##### Зацепка' that follows each NPC's stat-block).

Idempotent: if a marker comment is already present, skip.
"""
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\User\Murder-in-the-Tavern")
CH1 = ROOT / "publication" / "murder" / "02-chapter-1.md"

# character -> (anchor line to insert BEFORE, and an optional 'after' marker
# that must appear earlier in the file so we pick the right occurrence).
ANCHORS = {
    # dukstatar: insert before the '##### GM knows' that FOLLOWS the existing
    # '##### Вопросы и ответы (L1–L5)' heading (there are several 'GM knows').
    "dukstatar": ("##### GM knows", "##### Вопросы и ответы (L1–L5)"),
    "capitan": ("##### Зацепка: «Поиск дезертира»", None),
    "doctor_assistant": ("##### Зацепка: «Доктор в таверне»", None),
    "vassindio": ("##### Зацепка: «Поиск нелегальной контрабанды»", None),
}

MARKER = "{marker}"  # placeholder; we use a per-char marker


def insert_before(txt: str, anchor: str, after_marker, block: str,
                  marker: str) -> tuple[str, bool]:
    lines = txt.split("\n")
    # if 'after' marker is required, only match anchor lines that come AFTER
    # the last occurrence of the after-marker.
    start = 0
    if after_marker:
        for i, ln in enumerate(lines):
            if after_marker in ln:
                start = i + 1
    for i in range(start, len(lines)):
        if lines[i].strip() == anchor:
            if marker in txt:
                return txt, False  # already inserted
            out = lines[:i]
            out.append("")
            out.append(block.rstrip("\n"))
            out.append("")
            out += lines[i:]
            return "\n".join(out), True
    return txt, False


def main():
    txt = CH1.read_text(encoding="utf-8")
    for cid, (anchor, after_marker) in ANCHORS.items():
        block_path = ROOT / "generators" / ("_answers_" + cid + ".md")
        block = block_path.read_text(encoding="utf-8").rstrip("\n") + "\n"
        marker = "<!-- answers:%s -->" % cid
        full = marker + "\n" + block
        new, ok = insert_before(txt, anchor, after_marker, full, marker)
        if ok:
            txt = new
            CH1.write_text(txt, encoding="utf-8")
            print("inserted %s before '%s'" % (cid, anchor))
        else:
            print("skipped %s (already present or anchor missing)" % cid)


if __name__ == "__main__":
    main()
