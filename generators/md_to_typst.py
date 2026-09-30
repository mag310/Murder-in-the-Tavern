#!/usr/bin/env python3
"""Convert masters-book.md (PF2e source) to a Typst document using the
pf2e-style package (https://gitlab.com/Jed_Hed/pf2e-typst).

Strategy: a section-aware markdown->typst translator. Most content passes
through as Typst-native markup (Typst reads a large subset of Markdown
directly), but a handful of structural blocks are mapped to the package's
helpers:

    #### [PF2e stat-block]  ->  #encounter(...)   (stat-block table + abilities)
    #### Что зачитать / blockquote -> #aloud[...]  (read-aloud)
    #### GM knows / #### Куда / #### Зацепки  -> #note[...]

Output is written next to the source .md as <name>.typ.
"""

import os
import re
import sys
from pathlib import Path

# ---- PF2e stat-block field maps (Russian label -> typst detail line) ----

# Map the "Навыки" / ability rows to a single compact detail line.
SAVE_ROW = {
    "Спасброски": ("*Saves*", "saves"),
}

# Russian ability label -> short English-ish trait token used by the package.
# The package colours traits by token, so we keep PF2e-style tokens.
TRAIT_TOKENS = {
    "human": "Человек",
    "half-elf": "Полуэльф",
    "ghost": "Призрак",
    "cleric": "Жрец",
    "rogue": "Вор",
    "fighter": "Воин",
    "investigator": "Следователь",
    "champion": "Чемпион",
    "alchemist": "Алхимик",
}


def md_bold(s: str) -> str:
    """**text** -> *text* (Typst emphasis)."""
    return s


def read_block(lines: list[str], i: int) -> tuple[int, list[str]]:
    """Collect the contiguous lines belonging to one block, starting at lines[i].
    Returns the next index and the block lines."""
    j = i
    block = []
    while j < len(lines):
        ln = lines[j]
        # Stop at the next heading or a hard stop.
        if re.match(r"^#{1,6}\s", ln.strip()):
            break
        if ln.strip() == "---":
            # Horizontal rule — stop the block (it separates sections).
            break
        block.append(ln)
        j += 1
    return j, block


def parse_table(block: list[str]) -> dict[str, str]:
    """Parse a 2-column markdown table into {key: value}."""
    rows = {}
    for ln in block:
        m = re.match(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|", ln)
        if not m:
            continue
        key, val = m.group(1).strip(), m.group(2).strip()
        key = key.strip("*").strip()
        # Skip the separator row.
        if set(val) <= set("-: "):
            continue
        # Skip the header row.
        if key in ("Параметр", "Parameter"):
            continue
        rows[key] = val
    return rows


def ability_lines_to_details(abilities: list[str]) -> list[str]:
    """Convert a list of markdown bullet abilities into typst detail lines.
    Each bullet: - **Name (N actions):** text  ->  *Name* #A ... text
    The package shows action icons via #A / #AA / #AAA / #R / #F.
    """
    out = []
    for b in abilities:
        b = b.strip()
        if not b:
            continue
        m = re.match(r"^-\s+\*\*(.+?)\*\*(.*)", b)
        if not m:
            out.append(b)
            continue
        name, rest = m.group(1).strip(), m.group(2).strip()
        # Detect action economy markers in the name/first clause.
        icon = ""
        low = (name + rest).lower()
        # We do not auto-inject icons to avoid mislabelling; leave them out
        # unless a clear "реакция"/"1 действие" marker is present.
        if re.search(r"\bреакция\b", low):
            icon = " #R"
        elif re.search(r"\b2 действия?\b|\bдва действия?\b", low):
            icon = " #AA"
        elif re.search(r"\b1 действие\b|\bодно действие\b", low):
            icon = " #A"
        elif re.search(r"\b3 действия?\b|\bтри действия?\b", low):
            icon = " #AAA"
        text = (rest or "").lstrip(":").strip()
        line = f"*{name}{icon}*"
        if text:
            line += f" {text}"
        out.append(line)
    return out


def split_abilities(abilities: list[str]) -> list[str]:
    """Split a single bullet that wraps across multiple physical lines into
    one logical ability (continuation lines start with spaces, not '-')."""
    merged = []
    cur = ""
    for a in abilities:
        a = a.rstrip()
        if a.startswith("- ") or a.startswith("-\t"):
            if cur:
                merged.append(cur)
            cur = a[2:]
        elif a.strip() == "":
            if cur:
                merged.append(cur)
                cur = ""
        else:
            if cur:
                cur += " " + a.strip()
            else:
                cur = a.strip()
    if cur:
        merged.append(cur)
    return merged


def parse_stat_block(block: list[str]) -> str:
    """Build a #encounter(...) call from a [PF2e stat-block] section."""
    rows = parse_table(block)

    # Name: line like **Гаэтано Вельди — Трактирщик (NPC 5)**
    name = rows.get("Персонаж", "")
    # Try to pull a name from the **bold** line above the table.
    m = re.search(r"\*\*(.+?)\s*\(NPC\s*(\d+)\)", "\n".join(block))
    if m:
        full_name = m.group(1).strip()
        npc_level = m.group(2)
    else:
        full_name = rows.get("Персонаж", rows.get("Name", "NPC"))
        npc_level = rows.get("Уровень", "")

    # Build name "Имя — Роль".
    role = rows.get("Роль", "")
    if role:
        name = f"{full_name}"
    else:
        name = full_name

    # Trait tokens: race + alignment + a few role hints.
    race = rows.get("Раса", "")
    alignment = rows.get("Мировоззрение", "")
    traits = []
    if race:
        traits.append(race)
    # Role -> trait
    role_short = role
    if "Caster" in role or "Жрец" in role:
        traits.append("Жрец")
    if "rogue" in role.lower() or "Вор" in role:
        traits.append("Вор")
    if "boss" in role.lower() or "boss" in role:
        traits.append("Босс")
    traits = list(dict.fromkeys(traits))  # dedupe, keep order
    traits_str = ", ".join(traits)

    # Compose detail lines in PF2e stat-block order.
    details = []

    def row(k):
        return rows.get(k, "")

    if row("Восприятие"):
        details.append(f"*Perception* {row('Восприятие')}")
    if row("Языки"):
        details.append(f"*Languages* {row('Языки')}")
    if row("Навыки"):
        details.append(f"*Skills* {row('Навыки')}")

    # Ability scores line.
    stats = []
    for k, abbr in [("Сила", "Str"), ("Ловкость", "Dex"), ("Телосложение", "Con"),
                     ("Интеллект", "Int"), ("Мудрость", "Wis"), ("Харизма", "Cha")]:
        v = row(k)
        if v:
            stats.append(f"*{abbr}* {v}")
    if stats:
        details.append(", ".join(stats))

    if row("Скорость"):
        details.append(f"*Speed* {row('Скорость')}")
    if row("AC"):
        details.append(f"*AC* {row('AC')}")
    if row("HP"):
        details.append(f"*HP* {row('HP')}")

    if row("Спасброски"):
        details.append(f"*Saves* {row('Спасброски')}")

    # Divider
    details.append("[---]")

    if row("Ближний бой"):
        details.append(f"*Melee* {row('Ближний бой')}")
    if row("Дальний бой"):
        details.append(f"*Ranged* {row('Дальний бой')}")
    if row("СЛ заклинаний"):
        details.append(f"*DC* {row('СЛ заклинаний')}")
    if row("Атака заклинанием"):
        details.append(f"*Spell Attack* {row('Атака заклинанием')}")

    # Abilities section (bulleted list after "Способности:").
    abilities_raw = []
    in_abilities = False
    for ln in block:
        if re.match(r"^\*\*Способности[:：]?\*\*", ln.strip()) or re.match(r"^\*\*Заклинания", ln.strip()):
            in_abilities = True
            continue
        if in_abilities:
            stripped = ln.strip()
            if stripped.startswith("- "):
                abilities_raw.append(ln.rstrip())
            elif stripped == "":
                continue
            elif re.match(r"^\s+-\s", ln):
                # nested bullet (continuation of an ability)
                if abilities_raw:
                    abilities_raw[-1] = abilities_raw[-1] + " " + stripped.lstrip("- ").strip()
            else:
                # non-bullet line ends the abilities block
                if not re.match(r"^\s*\*", ln.strip()):
                    break
    abilities = split_abilities(abilities_raw)
    for a in ability_lines_to_details(abilities):
        # Inside a bracketed detail cell, `**x**` must become *x* (Typst
        # emphasis). Any leftover `**` would break the content delimiters.
        a = a.replace("**", "*")
        details.append(a)

    # Spell list (if present).
    if row("СЛ заклинаний") or any("Заклинания" in b for b in block):
        pass  # handled by abilities bullets already

    # Join details as a tuple of bracketed content items.
    details_str = ", ".join(
        f"[{d}]" if not d.startswith("[") else d for d in details
    )

    # The name line in the table can include " — Роль (NPC N)"; use the bold name.
    name_clean = full_name

    return (
        f"#encounter((\n"
        f"  name: [{name_clean}],\n"
        f"  type: [NPC {npc_level}],\n"
        f"  traits: ([{traits_str}]),\n"
        f"  details: ({details_str}),\n"
        f"))"
    )


def render_blockquote(text: str) -> str:
    """A read-aloud blockquote becomes #aloud[ ... ]."""
    text = re.sub(r"^\s*\n", "", text)
    # Markdown **bold** -> Typst *emphasis* (global, handles line breaks).
    text = text.replace("**", "*")
    text = text.replace("\n", "\n\n")
    return f"#aloud[\n{text}\n]"


def render_note(title: str, body: str) -> str:
    body = body.strip()
    if not body:
        return ""
    # Inside a #note[...] block, any [ ... ] would close the content early.
    # Replace [big]/[small]/[confidence: ...] style markers with braces.
    body = re.sub(r"\[([A-Za-z]+(?:\s*:[^\]]*)?)\]", r"{\1}", body)
    # Markdown **bold** inside the note body must become Typst *emphasis*.
    # Use a global ** -> * replacement (handles bold that spans line breaks).
    body = body.replace("**", "*")
    return f"#note[\n{body}\n]"


def typst_inline(line: str) -> str:
    """Convert a single markdown line to Typst-friendly inline markup."""
    s = line
    # images: ![alt](path) -> image(path, ...)
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'#image("\2", width: 80%)', s)
    # headings are handled separately; inline **bold** -> *bold*
    # Use a global ** -> * replacement so bold that spans line breaks is
    # also fixed (a single ** left in the stream confuses the parser).
    s = s.replace("**", "*")
    return s


def convert(md_text: str) -> str:
    lines = md_text.split("\n")
    out: list[str] = []
    out.append('#import "@preview/pf2e-style:0.2.0": *')
    out.append("#show: pf-stylization")
    out.append("")

    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        stripped = ln.strip()

        # ---- [PF2e stat-block] section ----
        if stripped == "#### [PF2e stat-block]":
            # Collect until next "#### " heading.
            j = i + 1
            block = []
            while j < n:
                if re.match(r"^#{1,6}\s", lines[j].strip()):
                    break
                if lines[j].strip() == "---":
                    break
                block.append(lines[j])
                j += 1
            out.append(parse_stat_block(block))
            i = j
            continue

        # ---- blockquote read-aloud (#### Что зачитать / #### Зачитать / >) ----
        if stripped.startswith("####") and re.search(
            r"Зачитать|Что зачитать|GM knows|Куда ведёт|Зацепки|Улики|Входы|Наблюдения|Атмосфера|Тактика|Тайны|История|Обитатели|Скрытое",
            stripped,
        ):
            title = stripped.lstrip("#").strip()
            # collect the block body until next heading
            j = i + 1
            body_lines = []
            while j < n:
                if re.match(r"^#{1,6}\s", lines[j].strip()):
                    break
                if lines[j].strip() == "---":
                    break
                body_lines.append(lines[j])
                j += 1
            body = "\n".join(body_lines).strip()
            # If the body is itself a blockquote (lines starting with '>'),
            # or the title says "зачитать", render as #aloud.
            is_read = re.search(r"Зачитать|Что зачитать", title) or (
                body.startswith(">")
            )
            if is_read and body:
                # strip leading '>' markers
                clean = re.sub(r"^>\s?", "", body, flags=re.MULTILINE)
                out.append(render_blockquote(clean))
            else:
                # render as a note box
                out.append(render_note(title, body))
            i = j
            continue

        # ---- headings ----
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            # level 1 (#) -> chap-header? we just use a big heading
            if level == 1:
                out.append(f"= {text}")
            elif level == 2:
                out.append(f"= {text}")
            elif level == 3:
                out.append(f"== {text}")
            elif level == 4:
                out.append(f"=== {text}")
            elif level == 5:
                out.append(f"==== {text}")
            else:
                out.append(f"===== {text}")
            i += 1
            continue

        # ---- blockquote lines (not under a heading) ----
        if stripped.startswith(">"):
            j = i
            bq = []
            while j < n and lines[j].strip().startswith(">"):
                bq.append(lines[j].strip()[1:].lstrip())
                j += 1
            clean = "\n".join(bq).strip()
            out.append(render_blockquote(clean))
            i = j
            continue

        # ---- horizontal rule ----
        if stripped == "---":
            out.append("#line(length: 100%)")
            i += 1
            continue

        # ---- markdown table (non stat-block) ----
        if re.match(r"^\|", ln) and i + 1 < n and re.match(r"^\|[\s\-:|]+\|", lines[i + 1]):
            # pass through as a typst table is complex; just emit the raw
            # grid as a typst table using #table. Simpler: emit as a
            # code-ish block so it stays readable.
            table_lines = [ln]
            k = i + 1
            while k < n and re.match(r"^\|", lines[k]):
                table_lines.append(lines[k])
                k += 1
            # Convert to #table by parsing.
            out.append(_md_table_to_typst(table_lines))
            i = k
            continue

        # ---- empty line ----
        if stripped == "":
            out.append("")
            i += 1
            continue

        # ---- normal paragraph / list ----
        # Join continuation lines of a paragraph.
        para = [ln]
        j = i + 1
        while j < n:
            nxt = lines[j]
            if nxt.strip() == "":
                break
            if re.match(r"^#{1,6}\s", nxt.strip()):
                break
            if nxt.strip().startswith("#### "):
                break
            if re.match(r"^\|", nxt.strip()):
                break
            if nxt.strip().startswith(">"):
                break
            if nxt.strip() == "---":
                break
            para.append(nxt)
            j += 1
        para_text = "\n".join(para).strip()
        para_text = typst_inline(para_text)
        out.append(para_text)
        i = j

    return "\n".join(out)


def _md_table_to_typst(table_lines: list[str]) -> str:
    """Convert a markdown grid table to a Typst #table[...] using grid."""
    rows = []
    for ln in table_lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue
        rows.append(cells)
    if not rows:
        return ""
    # Determine column count from header.
    ncol = len(rows[0])
    lines = []
    for r in rows:
        # pad/truncate to ncol
        while len(r) < ncol:
            r.append("")
        cells = [c.replace("**", "") for c in r[:ncol]]
        lines.append("  " + ", ".join(cells))
    # Use a simple grid; headers are the first row.
    header = rows[0]
    body = rows[1:]
    # Emit a simple Typst #table: header row in bold, body rows plain.
    # IMPORTANT: bold emphasis must be *inside* the content brackets, i.e.
    # [*Персонаж*], not [*Персонаж*] -> [*Персонаж*] (the latter makes Typst
    # read the trailing ] as an unclosed delimiter).
    out = [f"#table(columns: ({ncol} * 1fr)) ["]
    for idx, r in enumerate(rows):
        while len(r) < ncol:
            r.append("")
        cells = []
        for c in r[:ncol]:
            cell = c.replace("**", "")
            if idx == 0:
                cells.append(f"[*{cell}*]")
            else:
                cells.append(f"[{cell}]")
        out.append("  " + "  ".join(cells))
    out.append("]")
    return "\n".join(out)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: md_to_typst.py <input.md> [output.typ]", file=sys.stderr)
        return 2
    in_path = Path(sys.argv[1])
    if not in_path.exists():
        print(f"input not found: {in_path}", file=sys.stderr)
        return 2
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else in_path.with_suffix(".typ")
    md = in_path.read_text(encoding="utf-8")
    out = convert(md)
    out_path.write_text(out, encoding="utf-8")
    print(f"wrote {out_path} ({len(out)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
