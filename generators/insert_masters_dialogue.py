#!/usr/bin/env python3
"""Insert '#### Диалог' subsections into masters-book.md at the end of each
character's section (before the next '### ' heading).
"""
from pathlib import Path

ROOT = Path(r"C:\Users\User\Murder-in-the-Tavern")
MB = ROOT / "publication" / "masters-book.md"

# character -> the heading line that STARTS the NEXT section (insert before it)
# Each is unique.
NEXT_SECTION = {
    "dukstatar": "### Алессандро Маретти — Капитан «Чёрной Сирены»",
    "capitan": "### Тобиа Бандини — Ассистент Доктора",
    "doctor_assistant": "### Вассиндио Дровендж — Патриарх Совета Воров",
    "vassindio": "### Изабелла Вельди — Призрак",
}


def main():
    txt = MB.read_text(encoding="utf-8")
    for cid, next_heading in NEXT_SECTION.items():
        marker = "<!-- masters-dialogue:%s -->" % cid
        if marker in txt:
            print("skipped %s (already present)" % cid)
            continue
        block = (ROOT / "generators" / ("_masters_" + cid + ".md")).read_text(
            encoding="utf-8"
        ).rstrip("\n")
        # the _masters snippet starts with '#### Диалог: допрос ...'; make it
        # a '### ' level? No — keep as '####' (subsection of the '###' char).
        # Insert before the next '### ' heading.
        lines = txt.split("\n")
        idx = None
        for i, ln in enumerate(lines):
            if ln.strip() == next_heading:
                idx = i
                break
        if idx is None:
            print("MISSING anchor for", cid, next_heading)
            continue
        block_lines = [marker] + block.split("\n")
        # ensure blank line before block
        out = lines[:idx]
        out.append("")
        out += block_lines
        out.append("")
        out += lines[idx:]
        txt = "\n".join(out)
        MB.write_text(txt, encoding="utf-8")
        print("inserted %s dialogue before '%s'" % (cid, next_heading))


if __name__ == "__main__":
    main()
