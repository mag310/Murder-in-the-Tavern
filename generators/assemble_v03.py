#!/usr/bin/env python3
"""Assemble publication/v03/*.md into one Typst book (reuses md_to_typst)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import md_to_typst as m

root = Path(__file__).resolve().parent.parent
v03 = root / "publication" / "v03"
inputs = [
    v03 / "01-chapter-1.md",
    v03 / "02-1-B1.md",
    v03 / "03-1-B2.md",
    v03 / "04-1-B3.md",
    v03 / "05-1-B4.md",
    v03 / "06-1-C1.md",
    v03 / "07-1-C2.md",
    v03 / "08-1-C3.md",
    v03 / "09-1-C4.md",
    v03 / "10-1-D1.md",
    v03 / "11-1-D2.md",
    v03 / "12-1-D3.md",
    v03 / "13-1-D4.md",
    v03 / "13-1-E1.md",
    v03 / "14-1-E2.md",
    v03 / "15-1-E3.md",
    v03 / "16-1-E4.md",
    v03 / "16-1-F1.md",
    v03 / "17-1-F2.md",
    v03 / "18-1-F3.md",
    # Chapter 2 — tavern «Слёзы устрицы» (work in progress): overview + NPC cards + scene A1.
    v03 / "19-2-chapter-2.md",
    v03 / "20-2-npc.md",
    v03 / "21-2-A1.md",
    # Epilogue — after the chapter scenes, before the character dossiers.
    v03 / "79-4-epilogue.md",
    # Character dossiers — after the chapters, before the lore/bestiary block.
    v03 / "80-dossier.md",
    v03 / "85-detective-jacomo-ranieri.md",
    v03 / "86-artist-luciano-avrelian.md",
    v03 / "86-durotas-saria-roccin.md",
    # Bestiary and lore are always appended at the very end of the book.
    v03 / "90-lore.md",
    v03 / "91-Cheliax.md",
    v03 / "92-Westcrown.md",
    v03 / "93-dottari.md",
    v03 / "94-Order-of-the-Rack.md",
    v03 / "98-bestiarium.md",
]
missing = [p.name for p in inputs if not p.exists()]
if missing:
    print(f"missing inputs: {missing}", file=sys.stderr)
    raise SystemExit(2)

out_path = v03 / "book.typ"
# Convert each chapter via convert() (not assemble_book) so the first chapter's
# #chap-header does not get a leading #pagebreak (which would blank page 1).
parts = []
for p in inputs:
    parts.append(m.convert(p.read_text(encoding="utf-8")))
doc = m.PREAMBLE + "\n\n" + "\n\n".join(parts)
# The vendored pf2e-style package lives at publication/pf2e-style (one level up
# from v03), so fix the import path to resolve from v03/.
doc = doc.replace(
    '#import "pf2e-style/lib.typ"',
    '#import "../pf2e-style/lib.typ"',
)
out_path.write_text(doc, encoding="utf-8")
print(f"wrote {out_path} ({len(doc)} chars)")
