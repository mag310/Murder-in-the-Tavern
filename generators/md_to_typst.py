#!/usr/bin/env python3
"""Convert the *Murder in the Tavern* chapters to a Typst document (native, no
external package).

Source: the publication chapters live in ``publication/murder/*.md``.  Image
references inside those files use paths relative to that directory, e.g.
``../../locations/...`` and ``../../maps/...`` which resolve against the
repository root.  The output ``.typ`` is therefore written **next to the source
``.md``** (in ``publication/murder/``), and ``typst`` must be invoked with
``--root <repo>`` (done in ``main`` via ``typst`` CLI; see the README note at
the bottom of this file) so those relative paths resolve inside the sandbox.

Two modes:
    1. single file   -- md_to_typst.py <in.md> [<out.typ>]
    2. whole book    -- md_to_typst.py --book [<out.typ>]
                       concatenates 00-synopsis + 01-lore + 02-chapter-1 +
                       03-chapter-2 into one book.

The output begins with a preamble that imports a **vendored** copy of the PF2e
style package (``../vendor/pf2e-style/lib.typ`` — a local copy of
``@preview/pf2e-style:0.2.0`` with a one-line fix for Typst 0.15.x) and applies
``pf-stylization`` (2-column A4, Roboto body, green/red/maroon headings,
action-economy icons, and the ``#encounter`` / ``#aloud`` / ``#note`` /
``#pftab`` elements).  The build is therefore fully offline and reproducible.
The converted content maps to the package's elements:

    #### [PF2e stat-block]   ->  #encounter(...)   (PF2e creature stat-block)
    #### Что зачитать / >     ->  #aloud[ ... ]              read-aloud
    #### GM knows / ...       ->  #note[ ... ]               note
    markdown table           ->  #table(columns: ...) [ ... ] (real grid)

Robustness (the whole point of the rewrite): Typst's content delimiter is
``[`` / ``]`` and its emphasis delimiter is ``*``.  Two failure modes existed
before and are both fixed by the single ``escape`` rule below:

    * any stray ``[`` / ``]`` inside a bracketed block closes it early
      ("unclosed delimiter");
    * ``**bold**`` converted to ``*bold*`` can split across a line break,
      leaving an unbalanced ``*`` that closes an emphasis span.

So ``escape`` *removes* ``**`` outright (emphasis is dropped, never balanced)
and turns ``[`` / ``]`` into the safe ``{`` / ``}`` escapes.  It is applied to
every content fragment, so no ``*`` or ``[`` can ever break a block.
"""

import re
import sys
from pathlib import Path

# ---- PF2e stat-block field maps (Russian label -> typst detail line) ----
SAVE_ROW = {"Спасброски": ("Saves", "saves")}


def escape(s: str) -> str:
    # Typst markup-mode escapes for the characters that can break a
    # [...] content block or start a span/code/raw/math.
    for ch in "\\[]{}*_#$@`":
        s = s.replace(ch, "\\" + ch)
    return s

def neutralize(s: str) -> str:
    """Make plain text inert so it cannot break a Typst content block.

    * ``**`` is removed -- a lone/unbalanced ``*`` closes an emphasis span;
    * ``_`` is removed -- ``_`` starts an emphasis span too (e.g. an
      identifier ``kill_grid`` is read as ``kill`` + ``_grid...`` emphasis),
      and an unbalanced ``_`` -> "unclosed delimiter";
    * `` `` `` (backticks) are removed -- in a ``[...]`` block a backtick
      starts a raw string, and a raw string containing ``]`` or a line break
      yields "unclosed raw text" (this was the cause of the ``.json``
      failures);
    * a ``.`` after an identifier (e.g. ``flood_mechanic.json``) is parsed as
      a member access / call -> "unclosed delimiter"; replace it with ``:``
      so the text is inert.
    """
    s = s.replace("**", "")
    s = s.replace("`", "")
    s = s.replace("_", "")
    s = re.sub(r"(\w)\.", r"\1:", s)
    return s


def typst_inline(line: str) -> str:
    """Convert a single markdown line to Typst-friendly inline markup.

    Image spans are stashed *before* neutralisation so their paths (which
    contain ``.`` that :func:`neutralize` would turn into ``:``) survive;
    the rest of the line is neutralised and its brackets escaped, then the
    stashed image paths are re-inserted as ``#image(...)``.
    """
    images: list[str] = []

    def _stash(m: "re.Match[str]") -> str:
        images.append(m.group(2))
        return f"\x00IMG{len(images) - 1}\x00"

    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _stash, line)
    s = neutralize(s)
    s = escape(s)
    # Image paths must NOT be neutralised/escaped: neutralize() would turn
    # "flood_mechanic.json" dots into ":" (member access) and escape() would
    # backslash-escape every "." into a Typst path separator.  The raw path
    # is safe inside the #image("...") string argument.
    s = re.sub(
        r"\x00IMG(\d+)\x00",
        lambda m: f'#image("{images[int(m.group(1))].strip()}", width: 80%)',
        s,
    )
    return s


# ---- PF2e action-economy icons (from @preview/pf2e-style) -----------------
ICON_SINGLE = "#A"
ICON_DOUBLE = "#AA"
ICON_TRIPLE = "#AAA"
ICON_REACTION = "#R"
ICON_FREE = "#F"


def _clean(s: str) -> str:
    """Neutralise + escape a fragment for use inside a bracketed block, but
    do NOT flatten its parentheses (stat-block values keep their ``(…)``)."""
    s = neutralize(s)
    return escape(s)


def _icon_for(ability: str) -> str:
    """Pick an action-economy icon for an ability line (Russian text)."""
    low = ability.lower()
    if re.search(r"\b(реакция|реакц)\b", low):
        return ICON_REACTION
    if re.search(r"\b(2|два|две) действия\b|\b(2|два|две) действие", low):
        return ICON_DOUBLE
    if re.search(r"\b(3|три) действия\b|\b(3|три) действие", low):
        return ICON_TRIPLE
    if re.search(r"\b(1|одно|одна) действие\b", low):
        return ICON_SINGLE
    return ""


def _stat_table_to_rows(table_lines: list[str]) -> list[list[str]]:
    rows = []
    for ln in table_lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if not cells:
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        rows.append(cells)
    return rows


def parse_stat_block(block: list[str], heading: str = "") -> str:
    """Render a ``[PF2e stat-block]`` as a PF2e ``#encounter`` from
    ``@preview/pf2e-style`` (header + traits + a flat details column).

    The character name and d6 level come from the preceding
    "## Стат-блок: Name — Role (d6=N)" heading (``heading``); the block itself
    is only the stat table + abilities list.  ``rows`` is the parsed table.
    """
    rows = parse_table(block)

    # Name + level: from the heading just above the stat-block.  Two shapes:
    #   "## Стат-блок: Name — Role (d6=N)"  and  "#### NPC: Name"
    # NOTE: the "(d6=N)" is the d6 ID, NOT the character's level.  The real
    # level comes from the table's "Уровень" row, so we only take the NAME
    # from the heading here and read the level from the table below.
    name = "NPC"
    if heading:
        hm = re.search(r"Стат-блок:\s*(.+?)\s*\(d6\s*=\s*\d+\)", heading)
        if hm:
            name = hm.group(1).strip()
        else:
            hm = re.search(r"Стат-блок:\s*(.+?)\s*\(NPC\s*=\s*\d+\)", heading)
            if hm:
                name = hm.group(1).strip()
            else:
                hm = re.search(r"Стат-блок:\s*(.+)$", heading)
                if hm:
                    name = hm.group(1).strip()
        if name == "NPC":
            nm = re.search(r"NPC:\s*(.+?)\s*\(d6\s*=\s*\d+\)", heading)
            if nm:
                name = nm.group(1).strip()
            else:
                nm = re.search(r"NPC:\s*(.+)$", heading)
                if nm:
                    name = nm.group(1).strip()
    # Level: always the real character level from the table "Уровень" row.
    level = rows.get("Уровень", "")
    # Fallback: name from an in-block "**Name (d6=N)**" (never the d6 itself).
    if not name or name == "NPC":
        m = re.search(r"\*\*(.+?)\s*\(d6\s*=\s*\d+\)", "\n".join(block))
        if m:
            name = m.group(1).strip()

    # Ordered detail rows (label, value).
    ordered = [
        "Уровень", "Мировоззрение", "Раса", "Класс", "Роль", "Восприятие",
        "Языки", "Навыки", "Сила", "Ловкость", "Телосложение", "Интеллект",
        "Мудрость", "Харизма", "Скорость", "AC", "HP", "Спасброски",
        "Ближний бой", "Дальний бой", "СЛ заклинаний", "Атака заклинанием",
    ]
    details: list[str] = []
    used: set[str] = set()
    for key in ordered:
        val = rows.get(key, "")
        if val:
            used.add(key)
            details.append(f"*{key}* {val}")
    for k, v in rows.items():
        if k not in used and v:
            details.append(f"*{k}* {v}")

    # Abilities (bulleted list after "**Способности:" / "**Заклинания").
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
                if abilities_raw:
                    abilities_raw[-1] = abilities_raw[-1] + " " + stripped.lstrip("- ").strip()
            else:
                if not re.match(r"^\s*\*", ln.strip()):
                    break
    details = list(details)
    for a in ability_lines_to_details(split_abilities(abilities_raw)):
        a = a.strip()
        if not a:
            continue
        icon = _icon_for(a)
        details.append(f"{icon} *{a}" if icon else a)

    # Build the #encounter tuple.  Each detail is a single [ … ] content item
    # on its own line, followed by a comma (this Typst version does not accept
    # a comma-separated content list inside one [ … ]), and an entry equal to
    # "---" renders as a divider line.
    detail_items = []
    for line in details:
        text = _clean(line)
        if text == "---":
            detail_items.append("[---]")
        else:
            detail_items.append(f"[{text}]")
    details_code = "\n".join(f"    {it}," for it in detail_items)

    out = []
    out.append("#encounter((")
    out.append(f"  name: [{escape(name)}],")
    lvl = escape(str(level)).strip()
    out.append(f"  type: [{lvl}],")
    out.append("  traits: ([NPC]),")
    out.append("  details: (")
    out.append(details_code)
    out.append("  ),")
    out.append("))")
    return "\n".join(out)


def read_block(lines: list[str], i: int) -> tuple[int, list[str]]:
    """Collect the contiguous lines belonging to one block, starting at lines[i].
    Returns the next index and the block lines."""
    j = i
    block = []
    while j < len(lines):
        ln = lines[j]
        if re.match(r"^#{1,6}\s", ln.strip()):
            break
        if ln.strip() == "---":
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
        if set(val) <= set("-: "):
            continue
        if key in ("Параметр", "Parameter"):
            continue
        rows[key] = val
    return rows


def ability_lines_to_details(abilities: list[str]) -> list[str]:
    """Convert a list of markdown bullet abilities into typst detail lines."""
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
        icon = ""
        low = (name + rest).lower()
        if re.search(r"\bреакция\b", low):
            icon = " (реакция)"
        elif re.search(r"\b2 действия?\b|\bдва действия?\b", low):
            icon = " (2 действия)"
        elif re.search(r"\b1 действие\b|\bодно действие\b", low):
            icon = " (1 действие)"
        elif re.search(r"\b3 действия?\b|\bтри действия?\b", low):
            icon = " (3 действия)"
        text = (rest or "").lstrip(":").strip()
        line = f"{name}{icon}"
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


def render_blockquote(text: str) -> str:
    """A read-aloud blockquote becomes a PF2e ``#aloud`` (from the package)."""
    text = re.sub(r"^\s*\n", "", text)
    text = neutralize(text)
    text = escape(text)
    text = text.replace("\n", "\n\n")
    return f"#aloud[\n{text}\n]"


def render_note(title: str, body: str) -> str:
    body = body.strip()
    if not body:
        return ""
    title = neutralize(title)
    body = neutralize(body)
    return f"#note[\n{escape(title)}\n\n{escape(body)}\n]"


def _md_table_to_typst(table_lines: list[str]) -> str:
    """Convert a markdown grid table to a Typst ``#table`` that renders as a
    real table.  Every cell is escaped and its parentheses flattened so nothing
    can close the ``[...]`` cell list early."""
    rows = []
    for ln in table_lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if cells and set("".join(cells)) <= set("-: "):
            continue
        rows.append(cells)
    if not rows:
        return ""
    ncol = len(rows[0])

    cols = ", ".join(["1fr"] * ncol)          # -> "1fr, 1fr, 1fr"
    out: list[str] = ["#table(", f"  columns: ({cols}),"]
    for r in rows:
        while len(r) < ncol:
            r.append("")
        cells = [
            f"[{escape(neutralize(c).replace('(', ' - ').replace(')', ''))}]"
            for c in r[:ncol]
        ]
        out.append("  " + ", ".join(cells) + ",")
    out.append(")")
    return "\n".join(out)

def convert(md_text: str) -> str:
    lines = md_text.split("\n")
    out: list[str] = []

    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        stripped = ln.strip()

        # ---- [PF2e stat-block] section (### or #### heading) ----
        if re.sub(r"^#+\s+", "", stripped) == "[PF2e stat-block]":
            # The block itself is only the table + abilities.  The character
            # name/level live in a heading just above: either a
            # "## Стат-блок: Name — Role (d6=N)" heading or a "#### NPC: Name"
            # heading.  Scan upward to the nearest one and pass it in.
            heading = ""
            for k in range(i - 1, -1, -1):
                hm = re.match(r"^#{1,6}\s+(.*)$", lines[k].strip())
                if not hm:
                    continue
                h = hm.group(1).strip()
                if "Стат-блок" in h or re.match(r"^NPC:\s+", h):
                    heading = h
                    break
            j = i + 1
            block = []
            while j < n:
                if re.match(r"^#{1,6}\s", lines[j].strip()):
                    break
                if lines[j].strip() == "---":
                    break
                block.append(lines[j])
                j += 1
            out.append(parse_stat_block(block, heading=heading))
            i = j
            continue

        # ---- blockquote read-aloud / note (#### ... heading) ----
        if stripped.startswith("####") and re.search(
            r"Зачитать|Что зачитать|GM knows|Куда ведёт|Зацепки|Улики|Входы|Наблюдения|Атмосфера|Тактика|Тайны|История|Обитатели|Скрытое",
            stripped,
        ):
            title = stripped.lstrip("#").strip()
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
            is_read = re.search(r"Зачитать|Что зачитать", title) or body.startswith(">")
            if is_read and body:
                clean = re.sub(r"^>\s?", "", body, flags=re.MULTILINE)
                out.append(render_blockquote(clean))
            else:
                out.append(render_note(title, body))
            i = j
            continue

        # ---- headings ----
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            level = len(m.group(1))
            text = neutralize(m.group(2).strip())
            text = escape(text)
            prefix = "=" * min(level, 6)
            out.append(f"{prefix} {text}")
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
            table_lines = [ln]
            k = i + 1
            while k < n and re.match(r"^\|", lines[k]):
                table_lines.append(lines[k])
                k += 1
            out.append(_md_table_to_typst(table_lines))
            i = k
            continue

        # ---- empty line ----
        if stripped == "":
            out.append("")
            i += 1
            continue

        # ---- normal paragraph / list ----
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


# ---- PF2e-style package preamble -----------------------------------------
# We import a *vendored* copy of the package (vendor/pf2e-style) rather than
# "@preview/pf2e-style:0.2.0" so the build is offline and reproducible: the
# vendored copy carries a one-line local fix for the package's `pftraits`
# (.map on a single-element tuple, which fails on Typst 0.15.x).  The path is
# relative to the .typ output, which lives in publication/murder/, so
# ../vendor/... points back to the repo root.
PREAMBLE = '''#import "pf2e-style/lib.typ": *

// Apply the PF2e-Remastered look: 2-column A4, Roboto body, green/red/maroon
// headings, the action-economy icons (#A/#AA/#AAA/#R/#F) and the #encounter /
// #aloud / #note / #pftab elements used by the converted content below.
#show: pf-stylization
'''


import shutil


def _vendor_pf2e_style(out_dir: Path) -> None:
    """Copy the vendored pf2e-style package next to the .typ output so the
    package's own `#import "style/..."` and its action-icon SVG paths resolve
    relative to the .typ file (typst resolves image paths relative to the
    *input* file, not the imported module).  Done so the build is fully
    offline and reproducible."""
    root = Path(__file__).resolve().parent.parent
    src = root / "vendor" / "pf2e-style"
    dst = out_dir / "pf2e-style"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def assemble_book(paths: list[Path]) -> str:
    """Concatenate several chapter .md files into one Typst document, each
    starting on a new page.  Image paths stay relative to the first file's
    directory, so the output must be written alongside it (see main)."""
    parts = []
    for p in paths:
        md = p.read_text(encoding="utf-8")
        parts.append(convert(md))
    return PREAMBLE + "\n\n" + "\n\n".join(parts)


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(
            "usage: md_to_typst.py [--book] <input.md> [output.typ]\n"
            "       --book: assemble publication/murder/{00-synopsis,01-lore,"
            "02-chapter-1,03-chapter-2}.md into one book.\n"
            "       output (if omitted): <input>.typ (or murder_book.typ for "
            "--book), written next to the input so relative image paths "
            "resolve.\n"
            "       Compile with:  typst compile --root <repo> <out.typ> <out.pdf>\n"
            "       (--root is required so '../../.. image paths resolve "
            "inside the sandbox.)",
            file=sys.stderr,
        )
        return 2

    book = False
    positional = []
    for a in args:
        if a == "--book":
            book = True
        else:
            positional.append(a)

    if book:
        root = Path(__file__).resolve().parent.parent
        inputs = [
            root / "publication" / "murder" / f
            for f in ("00-synopsis.md", "01-lore.md", "02-chapter-1.md", "03-chapter-2.md")
        ]
        missing = [p.name for p in inputs if not p.exists()]
        if missing:
            print(f"missing inputs: {missing}", file=sys.stderr)
            return 2
        in_path = inputs[0]
        out_path = Path(positional[0]) if positional else in_path.with_name("murder_book.typ")
        doc = assemble_book(inputs)
    else:
        if len(positional) < 1:
            print("usage: md_to_typst.py <input.md> [output.typ]", file=sys.stderr)
            return 2
        in_path = Path(positional[0])
        if not in_path.exists():
            print(f"input not found: {in_path}", file=sys.stderr)
            return 2
        out_path = Path(positional[1]) if len(positional) > 1 else in_path.with_suffix(".typ")
        md = in_path.read_text(encoding="utf-8")
        doc = PREAMBLE + "\n\n" + convert(md)

    _vendor_pf2e_style(out_path.parent)
    out_path.write_text(doc, encoding="utf-8")
    print(f"wrote {out_path} ({len(doc)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
