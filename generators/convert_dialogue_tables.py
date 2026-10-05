#!/usr/bin/env python3
"""Convert dialogue markdown tables in the Murder chapters into `::: answers`
fenced blocks (the source form that md_to_typst.py turns into #answers-group).

A dialogue table is a markdown grid whose header row (after the question
column) carries candor/attitude columns.  Recognised shapes:

  multi-candor  | Вопрос | Hostile (L1) | Unfriendly (L2) | Indifferent (L3) | Friendly (L4) | Helpful |
  5-col plain   | Вопрос | Hostile | Unfriendly | Indifferent | Friendly | Helpful |
  5-col Lxx     | № | Вопрос | L1 (Hostile) | L2 (Unfriendly) | L3 (Indifferent) | L4 (Friendly) | L5 (Helpful) |
  single       | Вопрос | Ответ |
  single tone  | Вопрос | Ответ (Осторожный) |
  single level | Вопрос | Indifferent |

The output is a `::: answers` fenced block:

  ::: answers
  <NPC name or heading context>

  **Q:** <question text>
  <level>: <answer>
  [<level>: <answer>]...

  **Q:** ...
  :::

The NPC name is taken from the nearest preceding heading (####/#####/###).
Level keys map to the answers() signature in pf2e-style/lib.typ:
  Hostile  -> hostile      Unfriendly -> unfriendly   Indifferent -> indifferent
  Friendly -> friendly     Helpful    -> helpful
  L1..L5   -> hostile..helpful (by position)
  Ответ / Ответ (...) -> easy  (the single "Осторожный" default on the bridge)
  a lone level column (e.g. just "Indifferent") -> that level
"""
import re
import sys
from pathlib import Path

# Map a header cell (case-insensitive) to an answers() level key.
HEADER_TO_KEY = {
    "hostile": "hostile",
    "unfriendly": "unfriendly",
    "indifferent": "indifferent",
    "friendly": "friendly",
    "helpful": "helpful",
}

# A header cell is a "candor column" if its bare word (ignoring "(Lx)") is one
# of the known attitude names.
CANDOR_WORDS = set(HEADER_TO_KEY)

QUESTION_HEADERS = {"вопрос", "вопрос (осторожный)", "вопрос (friendly)"}


def is_question_header(col: str) -> bool:
    """True when the header cell is the question column (any variant)."""
    low = col.strip().lower().replace("**", "").strip()
    # exact match, or starts with "вопрос" (covers "вопрос / ситуация", etc.)
    return low in QUESTION_HEADERS or low.startswith("вопрос")


def _bare(col: str) -> str:
    """Strip markdown bold, quotes, parenthetical '(Lx)' / '(Friendly)'."""
    s = col.strip()
    s = s.replace("**", "")
    # drop a trailing "(...)"
    s = re.sub(r"\s*\(.*\)$", "", s).strip()
    return s.lower()


def is_dialogue_table(header_cells: list[str]) -> bool:
    """True when any header cell is 'Вопрос' (the question column).  The
    question column may be the first cell or (e.g. the Dukstatar table) be
    preceded by a '№' / number column."""
    return any(is_question_header(c) for c in header_cells)


def level_key_for(col: str) -> str | None:
    """Map a header cell to an answers() level key, or None if it is the
    question column or an unrecognised column."""
    low = col.strip().lower()
    # 0) bare "L1".."L5" (no candor word) -> position-based hostile..helpful
    m = re.match(r"^\s*l(\d)\s*$", low)
    if m:
        pos = int(m.group(1))
        if 1 <= pos <= 5:
            return ["hostile", "unfriendly", "indifferent", "friendly", "helpful"][pos - 1]
    # 1) try the bare word (e.g. "Hostile (L1)" -> "hostile")
    bare = _bare(low)
    bare = re.sub(r"^l\d+\s+", "", bare).strip()
    if bare in CANDOR_WORDS:
        return HEADER_TO_KEY[bare]
    # 2) the parenthetical itself may hold the candor word
    #    (e.g. "L1 (Hostile)" -> strip "L1" -> "(Hostile)" -> "hostile")
    paren = re.search(r"\(([^()]+)\)", low)
    if paren:
        p = paren.group(1).strip().lower()
        if p in CANDOR_WORDS:
            return HEADER_TO_KEY[p]
    # single "Ответ" / "Ответ (Осторожный)" -> the bridge default level 'easy'
    if bare in ("ответ",):
        return "easy"
    return None


def parse_table_rows(block: list[str]) -> list[list[str]]:
    """Parse a markdown grid block (including its separator row) into
    [header, data1, data2, ...] cell lists.  Drops the separator row."""
    rows = []
    for ln in block:
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        # separator row: all cells are only '-', ':', ' '
        if cells and set("".join(cells)) <= set("-: "):
            continue
        rows.append(cells)
    return rows


def nearest_heading_before(lines: list[str], idx: int) -> str:
    """Walk upward from `idx` to the nearest markdown heading line and return
    its text (bold/markdown stripped).  Used as the answers-group NPC name."""
    for k in range(idx - 1, -1, -1):
        m = re.match(r"^\s*#{1,6}\s+(.*)$", lines[k].strip())
        if m:
            txt = m.group(1).strip()
            txt = re.sub(r"\**", "", txt).strip()
            # trim trailing markers like "(d6=6)" / "(NPC 5)"
            txt = re.sub(r"\s*\(.*$", "", txt).strip()
            return txt
    return ""


def render_answers_group(npc: str, rows: list[list[str]], header: list[str]) -> str:
    """Render one answers-group from a parsed dialogue table.

    `rows` is the list of DATA rows (header already separated).  Each data row
    is [question, ans1, ans2, ...] aligned to the header columns.
    """
    # Find the question column (any cell that is a question header) and the
    # level columns (every other cell that maps to a level key).  A leading
    # '№' / number column (e.g. the Dukstatar table) is simply skipped.
    q_col = 0
    for i, col in enumerate(header):
        if is_question_header(col):
            q_col = i
            break

    col_keys: list[tuple[int, str]] = []
    for i, col in enumerate(header):
        if i == q_col:
            continue
        key = level_key_for(col)
        if key:
            col_keys.append((i, key))

    out: list[str] = ["::: answers"]
    if npc:
        out.append(npc)
    out.append("")

    for row in rows:
        if not row:
            continue
        if q_col >= len(row):
            continue
        q = row[q_col].strip()
        # strip surrounding ** bold markers (the question cell is "**Вопрос?**")
        q = q.replace("**", "").strip()
        if not q:
            continue
        out.append(f"**Q:** {q}")
        for col_idx, key in col_keys:
            if col_idx >= len(row):
                continue
            ans = row[col_idx].strip()
            if ans in ("", "—", "-", "— ", "—"):
                # empty / dash cells are omitted (the table had "—" for
                # "no answer at this level")
                continue
            # collapse internal newlines (there are none, but be safe)
            ans = re.sub(r"\s+", " ", ans).strip()
            out.append(f"{key}: {ans}")
        out.append("")
    out.append(":::")
    return "\n".join(out).rstrip() + "\n"


def find_table_span(lines: list[str], start: int) -> int:
    """From `start` (first table line), collect consecutive '|' lines into a
    block; return the index just past the block."""
    j = start
    while j < len(lines) and lines[j].strip().startswith("|"):
        j += 1
    return j


def is_separator_line(ln: str) -> bool:
    s = ln.strip()
    if not s.startswith("|"):
        return False
    cells = [c for c in s.strip("|").split("|")]
    joined = "".join(cells)
    return joined != "" and set(joined) <= set("-: ")


def main() -> int:
    root = Path(r"C:\Users\User\Murder-in-the-Tavern\publication\murder")
    for fname in ("02-chapter-1.md", "03-chapter-2.md"):
        path = root / fname
        txt = path.read_text(encoding="utf-8")
        lines = txt.split("\n")

        out_lines: list[str] = []
        i = 0
        n = len(lines)
        converted = 0
        while i < n:
            ln = lines[i]
            # A dialogue table starts at a header line containing "Вопрос".
            if ln.strip().startswith("|") and "Вопрос" in ln:
                # collect the table block
                j = find_table_span(lines, i)
                block = lines[i:j]
                rows = parse_table_rows(block)
                if rows:
                    header = rows[0]
                    data = rows[1:]
                    if is_dialogue_table(header) and data:
                        npc = nearest_heading_before(lines, i)
                        rendered = render_answers_group(npc, data, header)
                        # Preserve the blank line that preceded the table.
                        if out_lines and out_lines[-1] != "":
                            out_lines.append("")
                        out_lines.append(rendered)
                        converted += 1
                        i = j
                        continue
                # not a dialogue table (or unparseable): keep verbatim
                out_lines.append(ln)
                i += 1
                continue
            out_lines.append(ln)
            i += 1

        new_txt = "\n".join(out_lines)
        path.write_text(new_txt, encoding="utf-8")
        print(f"{fname}: converted {converted} dialogue table(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
