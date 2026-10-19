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
    # Chapter 2 — scenes/locations B–G (yard, tavern, second floor, mansard,
    # basement, dock) in reading order, right after the chapter intro.
    v03 / "22-2-B-yard.md",
    v03 / "23-2-B1-yard.md",
    v03 / "24-2-B2-stable.md",
    v03 / "25-2-B3-barn.md",
    v03 / "26-2-B4-well.md",
    v03 / "27-2-B5-woodpile.md",
    v03 / "28-2-B6-backyard.md",
    v03 / "29-2-B7-wife_grave.md",
    v03 / "29-2-B8-smugglers_cabin.md",
    v03 / "30-2-B9-staff_cabin.md",
    v03 / "30-2-C-tavern.md",
    v03 / "31-2-C1-tavern_hall.md",
    v03 / "32-2-C2-kitchen.md",
    v03 / "33-2-C3-office.md",
    v03 / "34-2-D-second.md",
    v03 / "35-2-D1-foyer.md",
    v03 / "36-2-D2-waitress_room.md",
    v03 / "37-2-D3-sailor_room.md",
    v03 / "38-2-D4-doctor_room.md",
    v03 / "39-2-D5-detective_room.md",
    v03 / "40-2-D6-tavern_keeper_room.md",
    v03 / "41-2-D7-guest_room_1.md",
    v03 / "42-2-D8-guest_room_2.md",
    v03 / "43-2-D9-guest_room_3.md",
    v03 / "44-2-E-mansard.md",
    v03 / "45-2-E1-artist_workshop.md",
    v03 / "46-2-E2-artist_room.md",
    v03 / "47-2-E3-attic_room_1.md",
    v03 / "48-2-E4-attic_room_2.md",
    v03 / "49-2-E5-attic_room_3.md",
    v03 / "50-2-E6-smoker_room.md",
    v03 / "51-2-F-basement.md",
    v03 / "52-2-F1-basement.md",
    v03 / "53-2-F2-kitchen_storage.md",
    v03 / "54-2-F3-meat_storage.md",
    v03 / "55-2-F4-wine_cellar.md",
    v03 / "56-2-F5-smuggler_storage.md",
    v03 / "57-2-F6-cult_lair.md",
    v03 / "58-2-G-quay.md",
    v03 / "59-2-G1-pier.md",
    v03 / "60-2-G2-shed.md",
    v03 / "61-2-G3-tunnel.md",
    v03 / "62-2-G4-quay.md",
    # Epilogue — after the chapter scenes, before the character dossiers.
    v03 / "79-4-epilogue.md",
    # Character dossiers — after the chapters, before the lore/bestiary block.
    v03 / "80-dossier.md",
    v03 / "81-tavern-keeper-gaetano-veldi.md",
    v03 / "82-sailor-korin-marrone.md",
    v03 / "83-waitress-vittoria-veldi.md",
    v03 / "84-doctor-elio-venturi.md",
    v03 / "85-detective-jacomo-ranieri.md",
    v03 / "86-artist-luciano-avrelian.md",
    v03 / "86-durotas-saria-roccin.md",
    v03 / "87-dead-wife-isabella-veldi.md",
    # Bestiary and lore are always appended at the very end of the book.
    v03 / "90-lore.md",
    v03 / "91-Cheliax.md",
    v03 / "92-Westcrown.md",
    v03 / "93-dottari.md",
    v03 / "94-Order-of-the-Rack.md",
    v03 / "95-Lacrime-della-madreperla.md",
    v03 / "96-cult-of-dagon.md",
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
