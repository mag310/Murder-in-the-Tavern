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

Why native Typst (and not the pf2e-style package): the package
``@preview/pf2e-style`` cannot be fetched offline, so ``#import`` fails and
``#aloud`` / ``#note`` / ``#encounter`` are "unknown variable".  We therefore
emit **native Typst** only:

    #### [PF2e stat-block]   ->  a #table(...) block (title + rows + abilities)
    #### Что зачитать / >     ->  #box(fill: gray.lighten(85%), [ ... ])   read-aloud
    #### GM knows / ...       ->  #box(stroke: 1pt, [ ... ])               note
    markdown table           ->  #table(columns: ...) [ ... ]            (real grid)

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
    """Escape ``{`` / ``}`` / ``[`` / ``]`` so they cannot break a Typst
    ``[...]`` content block.  This is the *only* transform that touches
    brackets, so it is safe to run on image paths too."""
    return s.replace("{", "{ {").replace("}", "} }").replace("[", "{").replace("]", "}")


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
    s = re.sub(
        r"\x00IMG(\d+)\x00",
        lambda m: f'#image("{escape(images[int(m.group(1))])}", width: 80%)',
        s,
    )
    return s


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


def parse_stat_block(block: list[str]) -> str:
    """Render a [PF2e stat-block] as a native Typst ``#table`` (title + rows +
    abilities).  No external package is used, so this always compiles offline.

    Every value is escaped and its parentheses are flattened (``(a)`` -> ``- a``)
    so nested ``(...)`` cannot break a Typst tuple/argument.
    """
    rows = parse_table(block)

    m = re.search(r"\*\*(.+?)\s*\(NPC\s*(\d+)\)", "\n".join(block))
    if m:
        name = m.group(1).strip()
        level = m.group(2)
    else:
        name = rows.get("Персонаж", rows.get("Name", "NPC"))
        level = rows.get("Уровень", "")

    # Ordered 2-column display rows (label, value).
    ordered = [
        ("Уровень", "Уровень"),
        ("Мировоззрение", "Мировоззрение"),
        ("Раса", "Раса"),
        ("Класс", "Класс"),
        ("Восприятие", "Восприятие"),
        ("Языки", "Языки"),
        ("Навыки", "Навыки"),
        ("Сила", "Сила"),
        ("Ловкость", "Ловкость"),
        ("Телосложение", "Телосложение"),
        ("Интеллект", "Интеллект"),
        ("Мудрость", "Мудрость"),
        ("Харизма", "Харизма"),
        ("Скорость", "Скорость"),
        ("AC", "AC"),
        ("HP", "HP"),
        ("Спасброски", "Спасброски"),
        ("Ближний бой", "Ближний бой"),
        ("Дальний бой", "Дальний бой"),
        ("СЛ заклинаний", "СЛ заклинаний"),
        ("Атака заклинанием", "Атака заклинанием"),
    ]
    table_rows = []
    for label, key in ordered:
        val = rows.get(key, "")
        if val:
            table_rows.append((label, val))
    # Any extra rows not in the ordered list (e.g. "Снаряжение", "Способности"
    # rendered as a cell) are appended as-is so nothing is lost.
    for k, v in rows.items():
        if k not in dict(ordered) and v:
            table_rows.append((k, v))

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
    abilities = [escape(neutralize(a)) for a in ability_lines_to_details(split_abilities(abilities_raw))]

    # Flatten nested parens so a value like "ЛН (Halfling)" can't break a tuple.
    def flatten(s: str) -> str:
        s = neutralize(s)
        s = s.replace("(", " - ").replace(")", "")
        s = escape(s)
        return s

    out = []
    out.append(f"= {escape(name)}" + (f" (NPC {escape(str(level))})" if level and level not in ("", "0") else ""))
    out.append("#table(columns: (2 * 1fr)) [")
    for label, val in table_rows:
        out.append(f"  [{flatten(label)}]  [{flatten(val)}]")
    out.append("]")
    if abilities:
        # Abilities are emitted as a plain list (not a #box): a #box with a
        # multi-line content block can fail to close in some contexts, and
        # plain content is always safe.
        out.append("")
        out.append("Способности:")
        for a in abilities:
            out.append(f"- {a}")
    return "\n".join(out)


def render_blockquote(text: str) -> str:
    """A read-aloud blockquote becomes a native #box (no external package)."""
    text = re.sub(r"^\s*\n", "", text)
    text = neutralize(text)
    text = escape(text)
    text = text.replace("\n", "\n\n")
    return f"#box(fill: gray.lighten(85%), inset: 1em, [\n{text}\n])"


def render_note(title: str, body: str) -> str:
    body = body.strip()
    if not body:
        return ""
    title = neutralize(title)
    body = neutralize(body)
    return f"#box(stroke: 1pt, inset: 0.5em, [\n{escape(title)}  {escape(body)}\n])"


def _md_table_to_typst(table_lines: list[str]) -> str:
    """Convert a markdown grid table to a Typst ``#table`` that renders as a
    real table.  Every cell is escaped and its parentheses flattened so nothing
    can close the ``[...]`` cell list early."""
    rows = []
    for ln in table_lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue
        rows.append(cells)
    if not rows:
        return ""
    ncol = len(rows[0])
    out = [f"#table(columns: ({ncol} * 1fr)) ["]
    for r in rows:
        while len(r) < ncol:
            r.append("")
        cells = [f"[{escape(neutralize(c).replace('(', ' - ').replace(')', ''))}]" for c in r[:ncol]]
        out.append("  " + "  ".join(cells))
    out.append("]")
    return "\n".join(out)


def convert(md_text: str) -> str:
    lines = md_text.split("\n")
    out: list[str] = []

    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        stripped = ln.strip()

        # ---- [PF2e stat-block] section ----
        if stripped == "#### [PF2e stat-block]":
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


def assemble_book(paths: list[Path]) -> str:
    """Concatenate several chapter .md files into one Typst document, each
    starting on a new page.  Image paths stay relative to the first file's
    directory, so the output must be written alongside it (see main)."""
    parts = []
    for p in paths:
        md = p.read_text(encoding="utf-8")
        parts.append(convert(md))
    return "\n\n".join(parts)


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
        doc = convert(md)

    out_path.write_text(doc, encoding="utf-8")
    print(f"wrote {out_path} ({len(doc)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
