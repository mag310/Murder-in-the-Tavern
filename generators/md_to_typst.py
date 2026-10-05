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
    #### Важно / Внимание     ->  #attention[ ... ]          attention
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


def _fmt(v: str) -> str:
    """Build a value fragment for a structured ``#encounter`` detail line.

    ``v`` is a raw stat-block value (already ``neutralize``-cleaned by the
    caller only when it is plain).  ``*`` is stripped here and the label /
    weapon name are bolded with explicit ``*…*`` spans, so the source must not
    contain ``**`` markup (``neutralize`` removes it).  The action icon is
    inserted right after the bold label via ``{icon} ``.
    """
    return v.replace("*", "")

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
    * a ``.`` *between* two word chars (e.g. ``flood_mechanic.json``,
      ``kill_grid._meta``) is parsed as member access / a call ->
      "unclosed delimiter"; replace *that* dot with ``:`` so the text is
      inert.  A sentence-final ``.`` (followed by a space, newline, ``:`` or
      end of text) is NOT a member access, so it is left untouched -- this is
      what made "город." render as "город:" before.
    """
    s = s.replace("**", "")
    s = s.replace("`", "")
    s = s.replace("_", "")
    # Only a dot sandwiched between two word chars is member access.  A dot
    # followed by a space / newline / end is a sentence end and stays a dot.
    s = re.sub(r"(\w)\.(\w)", r"\1:\2", s)
    return s


def typst_inline(line: str) -> str:
    """Convert a single markdown line to Typst-friendly inline markup.

    Image spans are stashed *before* neutralisation so their paths (which
    contain ``.`` that :func:`neutralize` would turn into ``:``) survive;
    the rest of the line is neutralised and its brackets escaped, then the
    stashed image paths are re-inserted as ``#image(...)``.
    """
    images: list[tuple[str, str]] = []  # (path, width-spec)

    def _stash(m: "re.Match[str]") -> str:
        inner = m.group(2).strip()
        # An optional trailing "NN%" sets the #image width; default 100%.
        wm = re.match(r"^(.*?)\s+(\d+%\s*)$", inner)
        if wm:
            path, width = wm.group(1).strip(), wm.group(2).strip()
        else:
            path, width = inner, "100%"
        images.append((path, width))
        return f"\x00IMG{len(images) - 1}\x00"

    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _stash, line)
    s = neutralize(s)
    s = escape(s)
    # Image paths must NOT be neutralised/escaped: neutralize() would turn
    # "flood_mechanic.json" dots into ":" (member access) and escape() would
    # backslash-escape every "." into a Typst path separator.  The raw path
    # is safe inside the #image("...") string argument.
    def _reinsert(m: "re.Match[str]") -> str:
        path, width = images[int(m.group(1))]
        return f'#image("{path}", width: {width})'

    s = re.sub(
        r"\x00IMG(\d+)\x00",
        _reinsert,
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


def _em(s: str) -> str:
    """Italicise a fragment (used for weapon names) inside a detail line.

    The fragment is escaped first so it is inert, then wrapped in ``_…_``.
    """
    return f"_{escape(s)}_"


def _esc(s: str) -> str:
    """Escape a fragment for a ``[...]`` block WITHOUT touching the action
    icons (``#A``/``#AA``/``#AAA``/``#R``/``#F``) that may sit at its start."""
    # Strip a leading action icon, escape the rest, re-attach the icon.
    m = re.match(r"^((?:#A+|#R|#F)\s*)", s)
    icon = m.group(1) if m else ""
    rest = s[m.end():] if m else s
    return icon + escape(rest)


def _icon_for(ability: str) -> str:
    """Pick an action-economy icon from an action note (the ability's name
    parenthetical, e.g. " (2 действия, 1/раунд)" or " (реакция)").

    Priority: reaction (#R) > 3-action (#AAA) > 2-action (#AA) > 1-action
    (#A) > free / passive / always-on (#F) > none.  Detection is based ONLY
    on the action note (never the description), so a description that happens
    to contain "реакция" (e.g. "цель реакции") does NOT force #R.
    """
    low = ability.lower()
    if re.search(r"\b(реакция|реакц)\b", low):
        return ICON_REACTION
    if re.search(r"\b(3|три) действия\b|\b(3|три) действие", low):
        return ICON_TRIPLE
    if re.search(r"\b(2|два|две) действия\b|\b(2|два|две) действие", low):
        return ICON_DOUBLE
    if re.search(r"\b(1|одно|одна) действие\b", low):
        return ICON_SINGLE
    # free / passive: auras, passive features (Sneak Attack, relics, …) or
    # any ability with no action cost.
    if re.search(r"\b(аура|passive|пассивн|free|без действия|свободн)\b", low):
        return ICON_FREE
    if not re.search(r"\b(1|2|3|одно|одна|два|две|три|действие|действия)\b", low):
        return ICON_FREE
    return ""


def _esc(s: str) -> str:
    """Escape a fragment for a ``[...]`` block WITHOUT touching the action
    icons (``#A``/``#AA``/``#AAA``/``#R``/``#F``) that may sit at its start."""
    # Strip a leading action icon, escape the rest, re-attach the icon.
    m = re.match(r"^((?:#A+|#R|#F)\s*)", s)
    icon = m.group(1) if m else ""
    rest = s[m.end():] if m else s
    return icon + escape(rest)


# Race -> trait (PF2e creature size is "Medium" / "Средний" for these NPCs).
_RACE_TRAITS = {
    "аасимар": ["Средний", "Аасимар", "Гуманоид"],
    "полуэльф": ["Средний", "Полуэльф", "Гуманоид"],
    "человек": ["Средний", "Человек", "Гуманоид"],
    "аасим": ["Средний", "Аасимар", "Гуманоид"],
}


def _split_value_parts(v: str) -> tuple[str, str]:
    """Split a stat value into (main, note).  A trailing parenthetical or a
    ';' / '|' separated clause is the note.  Returns (main, note)."""
    v = v.strip()
    # trailing parenthetical: "28 (high)" -> ("28", "high")
    m = re.search(r"^([^()]+?)\s*\(([^()]+)\)\s*$", v)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    # split on first ';' or '|'
    for sep in (";", "|"):
        if sep in v:
            a, b = v.split(sep, 1)
            return a.strip(), b.strip()
    return v, ""


def _attr_line(rows: dict) -> str:
    """Build the combined attributes line: *Сил* +N, *Лов* +N, … (short form)."""
    order = [("Сила", "Сил"), ("Ловкость", "Лов"), ("Телосложение", "Тел"),
             ("Интеллект", "Инт"), ("Мудрость", "Мдр"), ("Харизма", "Хар")]
    parts = []
    for full, short in order:
        val = rows.get(full, "")
        if val:
            parts.append(f"*{short}* {_esc(val.strip())}")
    return ", ".join(parts) if parts else ""


def _skills_line(rows: dict) -> str:
    """Build a single *Навыки* line with all skills as a comma-separated list,
    dropping the trailing proficiency tier in parentheses (high/moderate/…)."""
    raw = rows.get("Навыки", "")
    if not raw:
        return ""
    skills = []
    for part in re.split(r",\s*|;\s*", raw):
        s = part.strip()
        # drop a trailing "(tier)" annotation
        s = re.sub(r"\s*\((?:extreme|high|moderate|trained|expert|legends?)\)\s*$", "", s, flags=re.I)
        s = s.strip()
        if s:
            skills.append(s)
    return ", ".join(skills) if skills else ""


def _languages_line(rows: dict) -> str:
    val = rows.get("Языки", "")
    if not val:
        return ""
    langs = [x.strip() for x in re.split(r",\s*|;\s*", val) if x.strip()]
    return ", ".join(langs) if langs else ""


def _melee_line(rows: dict) -> str:
    """Compact melee line: *Ближний бой* #A _weapon_ +N (reach…), *Урон* …."""
    val = rows.get("Ближний бой", "")
    if not val:
        return ""
    val = _fmt(val)
    # weapon name = first token(s) before the first '+' attack bonus
    m = re.match(r"\s*([^\d+]+\??)\s*(\+.*?)$", val)
    if not m:
        return f"*Ближний бой* {escape(val)}"
    weapon = m.group(1).strip()
    attack = m.group(2).strip()
    # attack = "+18 (…)" — keep the parenthetical note (reach / two-handed)
    note = ""
    mm = re.search(r"\(([^)]+)\)\s*$", attack)
    if mm:
        note = f" ({mm.group(1).strip()})"
        attack = attack[:mm.start()].strip()
    # the #A icon must NOT be escaped: keep it, escape the rest
    return f"*Ближний бой* {ICON_SINGLE} {_em(weapon)} {escape(attack)}{escape(note)}"


def _ranged_line(rows: dict) -> str:
    val = rows.get("Дальний бой", "")
    if not val:
        return ""
    val = _fmt(val)
    m = re.match(r"\s*([^\d+]+\??)\s*(\+.*?)$", val)
    if not m:
        return f"*Дальний бой* {ICON_SINGLE} {escape(val)}"
    weapon = m.group(1).strip()
    attack = m.group(2).strip()
    note = ""
    mm = re.search(r"\(([^)]+)\)\s*$", attack)
    if mm:
        note = f" (метательное {mm.group(1).strip()})"
        attack = attack[:mm.start()].strip()
    return f"*Дальний бой* {ICON_SINGLE} {_em(weapon)} {escape(attack)}{escape(note)}"


def _saves_line(rows: dict) -> str:
    """Combine AC + the three saves into one line (PF2e stat-block style)."""
    ac = rows.get("AC", "")
    saves = rows.get("Спасброски", "")
    main, note = _split_value_parts(ac)
    ac_main = main or ac
    # saves may be "Стойкость +17; Реакция +16; Воля +17" or a table cell
    save_parts = []
    for s in re.split(r"[;|]\s*", saves):
        s = s.strip()
        if not s:
            continue
        s = re.sub(r"\s*\((?:extreme|high|moderate|trained|expert|legends?)\)\s*$", "", s, flags=re.I)
        save_parts.append(s)
    save_str = ", ".join(save_parts)
    line = f"*AC* {_esc(ac_main)}"
    if save_str:
        line += f"; {_esc(save_str)}"
    return line


def _hp_line(rows: dict) -> str:
    val = rows.get("HP", "")
    if not val:
        return ""
    main, _ = _split_value_parts(val)
    return f"*HP* {main or val}"


def _reaction_line(rows: dict) -> str:
    """Pull any reaction abilities out of the abilities list into a
    *Реакции* line.  Returns (reactions_line, filtered_abilities)."""
    return "", []


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

    # Name + level: from the heading just above the stat-block.  Shapes:
    #   "## Стат-блок: Name — Role (d6=N)"  /  "#### NPC: Name"
    #   "#### Статблок: Name — Creature N"  /  "#### Стражники доттари (…)"
    # NOTE: the "(d6=N)" / "(NPC=N)" / "(Creature N)" is an ID, NOT the
    # character's level.  The real level comes from the table's "Уровень"
    # row, so we only take the NAME from the heading here.
    name = ""
    if heading:
        # A "Стат-блок:" / "Статблок:" prefix (hyphen optional) + name.
        hm = re.search(r"Стат(?:-|)блок\s*:\s*(.+)", heading)
        if hm:
            name = hm.group(1).strip()
        else:
            # An "NPC: Name" heading.
            nm = re.search(r"NPC\s*:\s*(.+)", heading)
            if nm:
                name = nm.group(1).strip()
        # Any other heading IS the name (e.g. "Стражники доттари (4 бойца …)").
        if not name:
            name = heading.strip()
    # Level: always the real character level from the table "Уровень" row.
    level = rows.get("Уровень", "")
    # Fallback: name from an in-block "**Name (d6=N)**" (never the d6 itself).
    if not name:
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
    # A table row whose first cell is the "Способности" / "Заклинания" label is
    # NOT an ability header (e.g. "| **Способности** | Spell DC 25; ... |"); skip
    # it so the parameter line is not rendered as a spell.
    abilities_raw = []
    in_abilities = False
    for ln in block:
        # A blank line before the ability header (the table is separated from
        # the "**Способности:**" section by a blank line) must NOT stop the
        # scan — skip it so the header is still reached.
        if ln.strip() == "":
            continue
        if re.match(r"^\|", ln):
            if in_abilities:
                break
            continue
        stripped = ln.strip()
        # Header may carry trailing text (e.g. "**Способности:** _СЛ заклинаний 25; ..._"),
        # so match only the prefix, not the whole line.
        if re.match(r"^\*\*Способности[:：]?", stripped) or re.match(r"^\*\*Заклинания", stripped):
            in_abilities = True
            continue
        if in_abilities:
            if stripped.startswith("- "):
                abilities_raw.append(ln.rstrip())
            elif stripped == "":
                continue
            elif re.match(r"^\s+-\s", ln):
                if abilities_raw:
                    abilities_raw[-1] = abilities_raw[-1] + " " + stripped.lstrip("- ").strip()
            else:
                # a wrapped continuation line (indented, no leading "-"): merge
                # into the previous ability instead of dropping it.
                if re.match(r"\s+\S", ln):
                    if abilities_raw:
                        abilities_raw[-1] = abilities_raw[-1] + " " + stripped
                elif not re.match(r"^\s*\*", stripped):
                    break
    # --- Structured PF2e #encounter ------------------------------------------
    # `comp` fields: name, type, traits, details.  `details` is a tuple of
    # bracketed lines; a "[---]" entry renders as a divider in #encounter.
    level = str(level).strip() or "9"
    type_label = f"Существо {level}"

    # traits: a leading "Уникальный" tag + size / race / subtype.
    race = rows.get("Раса", "").strip().lower()
    traits = ["Уникальный"]
    traits += _RACE_TRAITS.get(race, ["Средний"])
    # dedup while preserving order
    seen: set[str] = set()
    traits = [t for t in traits if not (t in seen or seen.add(t))]

    # ---- detail lines (ordered, grouped with dividers) --------------------
    d: list[str] = []

    # 1) italic tag line (the character's one-line description / role).
    tag = _tag_line(rows)
    if tag:
        d.append(f"_{escape(tag)}_")

    # 2) Perception (with senses note if present).
    perception = rows.get("Восприятие", "")
    if perception:
        d.append(f"*Восприятие* {escape(_fmt(perception))}")

    # 3) languages (single combined line).
    langs = _languages_line(rows)
    if langs:
        d.append(f"*Языки* {escape(_fmt(langs))}")

    # 4) skills (single combined line).
    skills = _skills_line(rows)
    if skills:
        d.append(f"*Навыки* {escape(_fmt(skills))}")

    # 5) attributes (single combined line: Сил / Лов / Тел / Инт / Мдр / Хар).
    attrs = _attr_line(rows)
    if attrs:
        d.append(attrs)

    # 6) items (Предметы) — if present in the table.
    items = rows.get("Предметы", "")
    if items:
        d.append(f"*Предметы* {escape(_fmt(items))}")

    # 7) divider.
    d.append("[---]")

    # 8) AC + saves on one line.
    ac_line = _saves_line(rows)
    if ac_line:
        d.append(ac_line)

    # 9) HP on its own line.
    hp_line = _hp_line(rows)
    if hp_line:
        d.append(hp_line)

    # 10) reactions pulled from the abilities list.
    reactions = _reactions_line(abilities_raw)
    if reactions:
        d.append(reactions)

    # 11) divider.
    d.append("[---]")

    # 12) speed + melee + ranged (each its own line, with #A icons).
    speed = rows.get("Скорость", "")
    if speed:
        d.append(f"*Скорость* {escape(_fmt(speed))}")
    melee = _melee_line(rows)
    if melee:
        d.append(melee)
    ranged = _ranged_line(rows)
    if ranged:
        d.append(ranged)

    # 13) divider before the ability block.
    d.append("[---]")

    # 14) ability / spell lines (each "*Name* #icon **Частота** … description"),
    #     in source order.  Reaction abilities are rendered here as well as in
    #     the *Реакции* line (the *Реакции* line is the summary; the full text
    #     stays in the ability block, matching the PF2e stat-block layout).
    for a in ability_lines_to_details(split_abilities(abilities_raw)):
        a = a.strip()
        if not a:
            continue
        d.append(_ability_line(a))

    # ---- emit -------------------------------------------------------------
    out = [
        "#encounter((",
        f"  name: [{escape(name)}],",
        f"  type: [{escape(type_label)}],",
        "  traits: (" + ", ".join(f"[{escape(t)}]" for t in traits) + "),",
        "  details: (",
    ]
    for dl in d:
        # A divider is already a bracketed "[---]" element; wrapping it again
        # would produce "[[---]]", which does NOT match the `entry == [---]`
        # divider check in #encounter.  Emit it verbatim; wrap the rest.
        if dl == "[---]":
            out.append("    [---],")
        else:
            out.append(f"    [{dl}],")
    out.append("  ),")
    out.append("))")
    return "\n".join(out)


def _tag_line(rows: dict) -> str:
    """One-line italic tag: a 'Роль'/'Класс'/'Роль' description, or the class
    plus role.  Used for the italic line under the name header."""
    for key in ("Роль", "Класс", "Мировоззрение"):
        v = rows.get(key, "")
        if v:
            return v
    return ""


def _reactions_line(abilities_raw: list) -> str:
    """Pull reaction abilities from the raw bullet list into a single
    *Реакции* line (names only, comma-separated).  Returns "" if none."""
    names = []
    for b in abilities_raw:
        b = b.strip()
        low = b.lower()
        if not re.search(r"\bреакция\b", low):
            continue
        m = re.match(r"^-\s+\*\*(.+?)\*\*", b)
        if m:
            name = m.group(1).strip()
            # strip a trailing "(реакция)" / action note from the name
            name = re.sub(r"\s*\(.*$", "", name).strip()
            if name:
                names.append(name)
    if not names:
        return ""
    return "*Реакции* " + ", ".join(names)


def _ability_line(ability: str) -> str:
    """Render one ability bullet into a PF2e detail line:
    ``*Name* #icon … description``.

    ``ability`` is a clean ``"<Name> <description>"`` string (``split_abilities``
    already stripped "- " and "**").  The name may carry an action-economy
    note in parentheses (e.g. "Художественная казнь (2 действия, 1/раунд)").
    We keep that note with the name for the icon lookup, render the name
    (without the note), then the icon, then the description.
    """
    ability = ability.replace("**", "").strip()
    # The canonical form is "Name desc" where the name may carry an
    # action-economy note in parentheses (e.g. "Художественная казнь (2
    # действия, 1/раунд)") and may be separated from the description by a
    # ':' (e.g. "Аура освобождения: (аура, …)", "Оружие-реликвия «…»: +1
    # глефа …").
    #
    # Split the name from the description at ": " (a colon FOLLOWED BY A
    # SPACE).  A quoted name that ends in a colon, e.g.
    # "Оружие-реликвия «Шёпот Душ»:", has no ": " so it stays whole; only a
    # real description colon (": " + description) splits.
    split = ability.find(": ")
    if split >= 0:
        name = ability[:split].strip()
        rest = ability[split + 2:].strip()
    elif ":" in ability:
        # a lone ':' (no following space) is part of the name.
        name, rest = ability, ""
    else:
        name, rest = ability, ""
    # the icon is decided from the whole ability string: an explicit
    # action-economy marker — " (реакция)", " (N действие)" — may sit either
    # in the name (e.g. "Художественная казнь (2 действия, 1/раунд)") or in
    # the description (e.g. "Освобождающий шаг (реакция) …", "Ужасающее
    # присутствие (Frightful Presence) (1 действие): …").  Scanning the whole
    # string is reliable because such markers are never used in ordinary prose
    # here.  A blank note (no action cost) is a free / passive ability -> #F.
    icon = _icon_for(ability)
    # an ability with no explicit action cost is a free / passive ability
    # (an action "not requiring an action") -> #F.
    if not icon:
        icon = ICON_FREE
    line = f"*{escape(name)}*"
    if icon:
        line += f" {icon}"
    # drop the action marker(s) from the description so it is not shown twice
    # (e.g. "(реакция)", "(1 действие)"), then keep the description text.
    rest = re.sub(r"\s*\((реакция|реакц|1|2|3|одно|одна|два|две|три)[^)]*\)", "", rest, flags=re.I)
    rest = re.sub(r"\s+", " ", rest).strip()
    if rest:
        line += f" {_esc(rest)}"
    return line


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
    """Convert a list of markdown bullet abilities into a canonical ability
    string ``"<Name> <description>"``.

    The name keeps its full action-economy wording (e.g. "Художественная казнь
    (2 действия, 1/раунд)") so ``_icon_for`` / ``_ability_line`` can re-map it
    to the right ``#A`` / ``#AA`` / ``#R`` icon.  A leading "**…**" markdown
    bold and a trailing "**" are stripped.
    """
    out = []
    for b in abilities:
        b = b.strip()
        if not b:
            continue
        # ``split_abilities`` already stripped the leading "- " AND all "**"
        # bold markers, so ``b`` is a clean "Name desc" string.  Keep it
        # verbatim — ``_ability_line`` splits the name from the description.
        out.append(b)
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
            # strip ALL "**" markdown bold markers (e.g. "**Name:** desc" or
            # "**Name** desc") so the canonical string is a clean "Name desc";
            # the action-economy note stays with the name and _icon_for /
            # _ability_line re-map it to a typst icon.
            cur = cur.replace("**", "")
            cur = cur.strip()
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
    """A read-aloud blockquote becomes a PF2e ``#aloud`` (from the package).

    Paragraph breaks in the source markdown (a blank line between two
    paragraphs) become a Typst paragraph break (``\\n\\n``); a single newline
    (a hard-wrapped line in the middle of a paragraph) is collapsed to a
    space so it does not force a line break.  This keeps the read-aloud text
    flowing like the source rather than breaking at every source newline.
    """
    text = re.sub(r"^\s*\n", "", text)
    text = neutralize(text)
    # A blank line (one or more) is a paragraph break -> "\n\n".
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    # Any remaining single newline is a hard wrap -> collapse to a space.
    text = text.replace("\n", " ")
    # Collapse runs of spaces (but keep the "\n\n" paragraph breaks).
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()
    text = escape(text)
    return f"#aloud[\n{text}\n]"


def render_note(title: str, body: str) -> str:
    body = body.strip()
    if not body:
        return ""
    title = neutralize(title)
    body = neutralize(body)
    return f"#note[\n{escape(title)}\n\n{escape(body)}\n]"


def render_attention(title: str, body: str) -> str:
    body = body.strip()
    if not body:
        return ""
    title = neutralize(title)
    body = neutralize(body)
    return f"#attention[\n{escape(title)}\n\n{escape(body)}\n]"


# The candor/attitude level keys the `answers()` function in pf2e-style/lib.typ
# accepts, in the order the `answers()` signature lists them.  A `::: answers`
# block line `<key>: <text>` is rendered as a named argument of that key; any
# key not in this set is ignored (it would otherwise break the call).
_ANSWERS_KEYS = {
    "hostile", "unfriendly", "indifferent", "friendly", "helpful",
    "very_hard", "easy", "medium", "very_easy",
}


def _render_answers_group(buf: list[str]) -> str:
    """Render a collected `::: answers` block into a Typst ``#answers-group``.

    The block (between the opening `::: answers` and the bare `:::` close) has
    the shape::

        <NPC name>            # first non-empty line (optional)

        **Q:** <question>     # starts one `answers(...)`
        <level>: <answer>
        <level>: <answer>
        ...

        **Q:** <question>
        <level>: <answer>
        ...

    The first non-empty, non-`**Q:**` line is the NPC name (the
    `answers-group`'s only positional arg).  Each `**Q:**` starts a new
    `answers(...)` call; subsequent `<level>: <answer>` lines are its named
    arguments.  Every fragment is neutralised + escaped so no `[` / `]` / `*`
    can close a content block early (the answers() function takes bracketed
    content for `q` and each level).
    """
    # 1) strip the leading NPC-name line + blank lines: the first non-empty,
    #    non-`**Q:**` line is the NPC name; everything before the first **Q:**
    #    (other than the name) is ignored.
    body = [ln for ln in buf]
    # drop leading blank lines
    while body and body[0].strip() == "":
        body = body[1:]

    npc = ""
    if body and not body[0].lstrip().startswith("**Q:**"):
        npc = body[0].strip()
        npc = npc.replace("**", "").strip()
        body = body[1:]

    # 2) split the remaining lines into question groups.
    #    A `**Q:** <q>` line starts a new group; a `<key>: <answer>` line is
    #    appended to the current group.
    groups: list[dict] = []  # each: {"q": str, "levels": [(key, text), ...]}
    cur: dict | None = None
    for ln in body:
        s = ln.strip()
        if s == "":
            continue
        if s.startswith("**Q:") or s.startswith("**Q**"):
            # a **Q:** / **Q** question line.  The literal is "**Q:** text"
            # (i.e. "**" + "Q:" + "**"), so strip a leading "**Q**", "**Q:**",
            # or "**Q" then any trailing "**", colon and whitespace.
            q = re.sub(r"^\*\*\s*Q\s*:? ?\*?\*?\s*:?\s*", "", s, flags=re.IGNORECASE)
            q = q.replace("**", "").strip()
            cur = {"q": q, "levels": []}
            groups.append(cur)
            continue
        # a level line: `<key>: <answer>`
        m = re.match(r"^([a-z_]+)\s*:\s*(.*)$", s)
        if m and cur is not None:
            key, text = m.group(1), m.group(2).strip()
            if key in _ANSWERS_KEYS and text:
                cur["levels"].append((key, text))
            continue
        # a stray line (e.g. a wrapped answer continuation): append to the
        # current group's last level so it is not lost.
        if cur and cur["levels"]:
            cur["levels"][-1] = (
                cur["levels"][-1][0],
                (cur["levels"][-1][1] + " " + s).strip(),
            )

    # 3) emit the #answers-group call.  Every argument (the npc positional
    # arg and each `answers(...)` call) is followed by a comma so the
    # vararg list is well-formed; a trailing comma is allowed in Typst.
    parts: list[str] = []
    if npc:
        parts.append(f"  [{escape(neutralize(npc))}],")
    for g in groups:
        if not g["q"] and not g["levels"]:
            continue
        args = []
        if g["q"]:
            args.append(f"q: [{escape(neutralize(g['q']))}]")
        for key, text in g["levels"]:
            args.append(f"{key}: [{escape(neutralize(text))}]")
        # if there is a question but no levels (or vice-versa), still emit.
        if args:
            # trailing comma after the closing `)` so this is a valid vararg
            # element of the `..blocks` list (a trailing comma after the last
            # element is also allowed, so the final `answers(...)` is fine).
            parts.append("  answers(" + ", ".join(args) + "),")

    if not parts:
        return ""
    return "#answers-group(\n" + "\n".join(parts) + "\n)"


def _md_table_to_typst(table_lines: list[str]) -> str:
    """Convert a markdown grid table to a Typst ``#table`` that renders as a
    real table.  Every cell is escaped and its parentheses flattened so nothing
    can close the ``[...]`` cell list early."""
    rows = _md_table_rows(table_lines)
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


def _md_table_rows(table_lines: list[str]) -> list[list[str]]:
    """Split raw markdown grid rows into cell lists, dropping separator rows."""
    rows = []
    for ln in table_lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if cells and set("".join(cells)) <= set("-: "):
            continue
        rows.append(cells)
    return rows


def _md_table_to_pftab(table_lines: list[str], name: str = "") -> str:
    """Convert a markdown grid table to a Typst ``#pftab`` (the PF2e-Remastered
    styled table: an uppercase title plus alternating row fills and a dark
    header row).  ``name`` becomes the table's title; if empty it is omitted."""
    rows = _md_table_rows(table_lines)
    if not rows:
        return ""
    ncol = len(rows[0])

    cols = ", ".join(["1fr"] * ncol)          # -> "1fr, 1fr, 1fr"
    out: list[str]
    if name:
        out = [f"#pftab([{escape(name)}], columns: ({cols}),"]
    else:
        out = [f"#pftab(columns: ({cols}),"]
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

# Module-global flag: has at least one level-1/2/3 heading already been
# emitted?  The first one of the whole document does NOT get a page break
# (it would leave page 1 empty); from the second heading onward a
# #page.break() is emitted before the heading.
_PAGE_BROKEN = False

# Module-global fence state.  `_FENCE` tracks the currently open `:::` fence
# ("one-col" / "pftab" / "answers" / None); `_PFTAB_NAME` holds the title for a
# pftab fence; `_ANSWERS_BUF` accumulates the lines of an `::: answers` block.
_FENCE = None
_PFTAB_NAME = ""
_ANSWERS_BUF: list[str] = []

# The most recent heading text, used to title auto-wrapped `#pftab` tables.
_last_heading = ""


def _extract_pftab_name(stripped: str) -> str:
    """Pull the table title out of a `::: pftab[Title]` fence line, e.g.
    `::: pftab[Весткроун]` -> "Весткроун".  Empty when no title is given."""
    m = re.search(r"\[([^\]]*)\]", stripped)
    return neutralize(m.group(1).strip()) if m else ""


# Table-classification helpers used to auto-wrap every markdown table in a
# `::: pftab` (styled table) and/or `::: one-col` (full-width single column)
# fence, so the author does not have to annotate each table by hand.
_PFTAB_HEADER_COLS = {"УРОВЕНЬ", "ЗАКЛ. УРОВНЯ", "УРОВЕНЬ/ЗАКЛ. УРОВНЯ"}

# Headings whose table is a *stat block* (character/creature/NPC stat sheet).
# These render as a `#statblock`, so they must NOT be turned into a `#pftab`.
_STATBLOCK_HEADINGS = (
    "Стат-блок", "Статблок", "Статблок:", "NPC:", "NPC ", "NPC.",
)

_DIALOGUE_HDR = "Вопрос"
_DIALOGUE_COL = "Ответ"
# Columns that name an attitude/level bucket, i.e. a table whose body cells are
# spoken dialogue lines keyed by candor/attitude (the "dialogue tables").
_ATTITUDE_COLS = {
    "Hostile", "Unfriendly", "Indifferent", "Friendly", "Helpful",
    "Осторожный", "Доверяет", "Не доверяет",
}


def _pftab_name(table_lines: list[str], context: dict) -> str:
    """Derive the `#pftab` title for a table.  Prefers the nearest preceding
    heading; falls back to a label from the header row (e.g. "Весткроун")."""
    h = context.get("heading")
    if h:
        return neutralize(h)
    # 2-col tables whose first header cell is a plain proper noun (e.g. the
    # "Весткроун | Город" facts table) -> use that cell as the title.
    if len(context.get("header_cells", [])) == 2:
        c0 = neutralize(context["header_cells"][0])
        if c0 and c0.isupper() is False and not c0.startswith("**"):
            return c0
    return context.get("heading") or "Таблица"


def _header_cells(table_lines: list[str]) -> list[str]:
    """The table's header row cells (the first non-separator row)."""
    for ln in table_lines:
        s = ln.strip()
        if re.match(r"^\|[\s\-:|]+\|", s):
            continue  # separator row
        return [c.strip() for c in s.strip("|").split("|")]
    return []


def is_dialogue(table_lines: list[str], context: dict) -> bool:
    """True when a table is a *dialogue* table (question/answer or
    question-by-attitude), which must be rendered in a single full-width
    column so the spoken lines are not split across the 2-column page."""
    hdr = context.get("header_cells", [])
    cols = [c.strip() for c in hdr]
    if _DIALOGUE_HDR in cols:
        return True
    if _DIALOGUE_COL in cols:
        return True
    if _ATTITUDE_COLS.intersection(c.strip() for c in cols):
        return True
    return False


def _is_statblock(context: dict) -> bool:
    """True when the table sits under a stat-block heading (stat sheet)."""
    h = context.get("heading", "")
    return any(h.startswith(s) for s in _STATBLOCK_HEADINGS)


def convert(md_text: str, page_broken: bool = False) -> str:
    global _PAGE_BROKEN, _FENCE, _PFTAB_NAME, _ANSWERS_BUF, _last_heading
    _FENCE = None
    _PFTAB_NAME = ""
    _ANSWERS_BUF = []
    # `_last_heading` is reset per `convert()` call so that the first table of
    # each chapter file does not inherit the last heading of the previous file
    # (the assembled book calls `convert()` once per chapter).
    _last_heading = ""
    lines = md_text.split("\n")
    out: list[str] = []

    i = 0
    n = len(lines)
    if page_broken:
        _PAGE_BROKEN = True
    while i < n:
        ln = lines[i]
        stripped = ln.strip()

        # ---- inside a ::: answers fence: buffer verbatim until the close ----
        # The `::: answers` block is collected line-by-line (the NPC name, the
        # **Q:** question lines and the `<level>: <answer>` lines) and turned
        # into an #answers-group when the bare `:::` close is reached.  None of
        # the buffer lines may be re-processed by the handlers below.  The
        # closing `:::` is NOT consumed here — it must fall through to the
        # fence-close branch below so the group is actually emitted.
        if _FENCE == "answers" and not re.match(r"^:::\s*$", stripped):
            _ANSWERS_BUF.append(ln)
            i += 1
            continue

        # ---- [PF2e stat-block] section (### or #### heading) ----
        if re.sub(r"^#+\s+", "", stripped) == "[PF2e stat-block]":
            # The block itself is only the table + abilities.  The character
            # name/level live in a heading above the [PF2e stat-block] marker.
            # Strategy: scan upward and take the FIRST heading that is either an
            # explicit "Стат-блок"/"Статблок"/"NPC:" stat-block heading, or (if
            # none exists) the nearest heading that is NOT a per-character
            # sub-section (Идентификация / Скрывает / Хочет / Что зачитать /
            # Описание / …).  This keeps the right name for both the d6
            # characters (whose stat-block marker sits deep in the section, so
            # the nearest heading is a sub-section like "Хочет") and the unnamed
            # creatures (whose own heading is "Статблок: …" or "Стражники …").
            _SUBSECTIONS = (
                "Идентификация", "Скрывает", "Хочет", "Что зачитать",
                "Описание", "GM knows", "Наблюдения", "Атмосфера",
            )
            heading = ""
            for k in range(i - 1, -1, -1):
                nxt = lines[k].strip()
                hm = re.match(r"^#{1,6}\s+(.*)$", nxt)
                if not hm:
                    continue
                h = hm.group(1).strip()
                if re.search(r"Стат(?:-)?блок\s*:", h) or re.match(r"NPC\s*:", h):
                    heading = h
                    break
                if any(h.startswith(s) for s in _SUBSECTIONS):
                    continue
                # First non-sub-section heading above is the character's heading.
                heading = h
                break
            j = i + 1
            block = []
            # 1) collect the stat table (until the first heading or "---").
            while j < n:
                if re.match(r"^#{1,6}\s", lines[j].strip()):
                    break
                if lines[j].strip() == "---":
                    break
                block.append(lines[j])
                j += 1
            # 2) the abilities / spells live in a FOLLOWING sibling section
            #    ("**Способности:**" / "**Заклинания:**") — not inside the table
            #    block.  Absorb that section so parse_stat_block sees the
            #    abilities.  Skip any blank lines between the table and the
            #    abilities section.
            k = j
            while k < n and lines[k].strip() == "":
                k += 1
            if k < n and re.match(r"^\*\*(Способности|Заклинания)", lines[k].strip()):
                m = k + 1
                while m < n:
                    if re.match(r"^#{1,6}\s", lines[m].strip()):
                        break
                    if lines[m].strip() == "---":
                        break
                    block.append(lines[m])
                    m += 1
                j = m
            out.append(parse_stat_block(block, heading=heading))
            i = j
            continue

        # ---- read-aloud / attention / note heading (any level: ##, ###, ####, ...) ----
        # A heading whose title is a cue becomes an #aloud, #attention or #note.
        # Works for ANY heading level (the body may be a blockquote ">", plain
        # prose, or a mixed block).  Routing by title (a blockquote ">" body is
        # treated as read-aloud only when the title is NOT an attention cue):
        #   - "Зачитать"/"Что зачитать"              -> #aloud
        #   - "Важно"/"Внимание"                     -> #attention
        #   - a ">"-blockquote body (no other cue)   -> #aloud
        #   - other cues (GM knows, Наблюдения, …)   -> #note
        # Priority: "Зачитать" title > "Важно"/"Внимание" title > ">"-body > #note.
        # So a "Важно: …" block that is also a ">"-quote becomes #attention (a
        # technical caution), not #aloud, and a "Зачитать" title is always #aloud.
        if re.match(r"^#{1,6}\s", stripped) and re.search(
            r"Зачитать|Что зачитать|Важно|Внимание|GM knows|Куда ведёт|Зацепки|Улики|Входы|Наблюдения|Атмосфера|Тактика|Тайны|История|Обитатели|Скрытое",
            stripped,
        ):
            title = re.sub(r"^#+\s+", "", stripped).strip()
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
            is_read = re.search(r"Зачитать|Что зачитать", title)
            is_attention = re.search(r"Важно|Внимание", title)
            if is_read and body:
                clean = re.sub(r"^>\s?", "", body, flags=re.MULTILINE)
                out.append(render_blockquote(clean))
            elif is_attention and body:
                clean = re.sub(r"^>\s?", "", body, flags=re.MULTILINE)
                out.append(render_attention(title, clean))
            elif body.startswith(">") and body:
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
            # Page breaks before level-1/2/3 headings are handled by the
            # #show heading rule in pf2e-style/style/formatting.typ (which
            # prepends #page to every level 1/2/3 heading).  No break is
            # emitted here.
            pass
            # ---- chapter header (ANY level-1 heading) ----
            # A level-1 heading becomes a decorative #chap-header.  A "Глава N.
            # Title" heading splits into num + title; any other level-1 heading
            # uses the whole title as the title (num = "").  The description is
            # the next non-empty, non-heading, non-image line (usually the
            # "Таймлайн главы N: …" line); it is consumed so it is not
            # re-emitted as a normal paragraph.
            cm = re.match(r"^Глава\s+(\d+)\s*[.:]\s*(.*)$", text)
            if level == 1:
                if cm:
                    num = cm.group(1)
                    title = cm.group(2).strip() or text
                else:
                    num = ""
                    title = text
                # Look ahead for the description (next non-empty meaningful line).
                # Only a heading / image / "---" / ":::" fence STOPS the scan
                # (they are not the description and must NOT be consumed — an
                # image or a fence especially must stay in the flow to be
                # rendered); blank lines are skipped.
                desc = ""
                k = i + 1
                while k < n:
                    nxt = lines[k].strip()
                    if nxt == "":
                        k += 1
                        continue
                    if re.match(r"^#{1,6}\s", nxt):
                        break
                    # An image, a "---", or a `:::` fence: do NOT consume it —
                    # break so it is re-processed below (otherwise the image /
                    # fence would be lost, e.g. a `::: one-col` after the title).
                    # A *closing* `:::` (one-col) also ends the level-1 heading
                    # here: the heading stays inside the one-col block and renders
                    # as a normal `==` heading rather than a `#chap-header`.
                    if re.match(r"^!\[", nxt) or nxt == "---":
                        break
                    if re.match(r"^:::\s*$", nxt):
                        break
                    # An *opening* `:::` fence (one-col / pftab) must NOT be
                    # consumed as the description, but it is a full-width block
                    # start that belongs before this heading — skip it so the
                    # scan can reach the real description.
                    if re.match(r"^:::", nxt):
                        k += 1
                        continue
                    # The first real (non-image, non-heading, non-fence) line is
                    # the desc.
                    desc = re.sub(r"\**", "", nxt).strip()
                    k += 1
                    break
                title_txt = neutralize(title)
                title_txt = escape(title_txt)
                desc_txt = neutralize(desc)
                desc_txt = escape(desc_txt)
                # Quote all three args so colons / parens / punctuation in the
                # title or description cannot break the call's argument list.
                # The first level-1 heading of the whole document does NOT get a
                # page break before it -- it would leave page 1 empty.
                # If the chapter opens with a `::: one-col` fence (the description
                # scan stops at a `:::` fence), the `#set page(columns: 1)` that
                # the fence emits provides the full-width start on its own, so no
                # separate `#pagebreak()` is emitted before the chapter header.
                follow = ""
                for kk in range(k, n):
                    s = lines[kk].strip()
                    if s == "":
                        continue
                    follow = s
                    break
                if re.match(r"^:::\s*one-col\s*$", follow):
                    pass
                elif _PAGE_BROKEN:
                    out.append("#pagebreak()")
                else:
                    _PAGE_BROKEN = True
                out.append(
                    f"#chap-header(\"{escape(num)}\", "
                    f"\"{title_txt}\", \"{desc_txt}\")"
                )
                i = k
                continue
            prefix = "=" * min(level, 6)
            if level <= 3:
                # A page break before the heading (so the heading starts a new
                # page).  The very first heading of the whole document does NOT
                # get one -- it would leave page 1 empty.
                if _PAGE_BROKEN:
                    out.append("#pagebreak()")
                else:
                    _PAGE_BROKEN = True
            out.append(f"{prefix} {text}")
            # Remember the (raw, un-escaped) heading text so the next auto-wrapped
            # `#pftab` table can use it as the table title.  `neutralize`/`escape`
            # are applied later in `_md_table_to_pftab`, so store it un-escaped.
            _last_heading = re.sub(r"\**", "", m.group(2).strip())
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
            # A "Важно"/"Внимание" caution is a technical attention block, not a
            # read-aloud.  Detect it in the first line (bare or **bold**).
            first = re.sub(r"\**", "", bq[0]).strip() if bq else ""
            if re.search(r"Важно|Внимание", first):
                # The title already says "Важно", so drop a leading "Важно:" /
                # "Внимание:" marker (bold or bare) from the body to avoid
                # duplicating it.
                body = re.sub(r"^\s*\**\s*(?:Важно|Внимание)\s*\**\s*:?\s*", "", clean, count=1)
                out.append(render_attention("Важно", body))
            else:
                out.append(render_blockquote(clean))
            i = j
            continue

        # ---- horizontal rule ----
        if stripped == "---":
            out.append("#line(length: 100%)")
            i += 1
            continue

        # ---- fences: ::: one-col / ::: pftab[Title] / ::: answers … ::: ----
        # A single fence state machine.  `::: one-col` opens a full-width page
        # block (emits `#set page(columns: 1)`); `::: pftab[Title]` opens a
        # styled-table block that routes the next markdown table to `#pftab`;
        # `::: answers` opens an interrogation-answers block that emits an
        # `#answers-group(...)` (the PF2e-Remastered interrogation element).
        # A bare `:::` closes the most recent open fence.
        if re.match(r"^:::\s*one-col\s*$", stripped):
            _FENCE = "one-col"
            out.append("#set page(columns: 1)")
            i += 1
            continue
        if re.match(r"^:::\s*pftab\s*(\[[^\]]*\])?\s*$", stripped):
            _FENCE = "pftab"
            _PFTAB_NAME = _extract_pftab_name(stripped)
            i += 1
            continue
        if re.match(r"^:::\s*answers\s*$", stripped):
            _FENCE = "answers"
            _ANSWERS_BUF = []
            i += 1
            continue
        if re.match(r"^:::\s*$", stripped):
            if _FENCE == "one-col":
                out.append("#set page(columns: 2)")
            elif _FENCE == "answers":
                # Emit the answers-group in the normal flow.  `answers`/
                # `answers-group` render as a breakable block whose own
                # `table` lays out independently of the page's 2-column
                # flow, so no `#set page(columns: ...)` wrapper is needed.
                out.append(_render_answers_group(_ANSWERS_BUF))
                _ANSWERS_BUF = []
            _FENCE = None
            _PFTAB_NAME = ""
            i += 1
            continue

        # ---- markdown table (non stat-block) ----
        if re.match(r"^\|", ln) and i + 1 < n and re.match(r"^\|[\s\-:|]+\|", lines[i + 1]):
            table_lines = [ln]
            k = i + 1
            while k < n and re.match(r"^\|", lines[k]):
                table_lines.append(lines[k])
                k += 1

            if _FENCE == "pftab":
                # A manual `::: pftab[Title]` fence already wraps this table.
                out.append(_md_table_to_pftab(table_lines, name=_PFTAB_NAME))
                _FENCE = None
                _PFTAB_NAME = ""
            else:
                # Auto-wrap the table: every markdown table becomes a `#pftab`
                # (styled table); a *dialogue* table is additionally wrapped in
                # `::: one-col` so its spoken lines stay full-width.  Stat-block
                # sheets (under a "Стат-блок"/"NPC:" heading) are left as-is so
                # they still render as a `#statblock`.
                ctx = {"heading": _last_heading, "header_cells": _header_cells(table_lines)}
                if _is_statblock(ctx):
                    out.append(_md_table_to_typst(table_lines))
                else:
                    is_onecol = is_dialogue(table_lines, ctx)
                    if is_onecol:
                        out.append("#set page(columns: 1)")
                    out.append(_md_table_to_pftab(table_lines, name=_pftab_name(table_lines, ctx)))
                    if is_onecol:
                        out.append("#set page(columns: 2)")
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
            # A `:::` fence line must stop the paragraph so the fence branch can
            # process it (otherwise it would be absorbed into the paragraph).
            if re.match(r"^:::", nxt.strip()):
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
    """Copy the pf2e-style package next to the .typ output so the
    package's own `#import "style/..."` and its action-icon SVG paths resolve
    relative to the .typ file (typst resolves image paths relative to the
    *input* file, not the imported module).  Done so the build is fully
    offline and reproducible."""
    root = Path(__file__).resolve().parent.parent
    src = root / "vendor" / "pf2e-style"
    dst = out_dir / "pf2e-style"
    if not src.exists():
        # vendor/ is absent; the package already lives next to the .typ
        # output (publication/murder/pf2e-style), so there is nothing to copy.
        if dst.exists():
            return
        print(
            f"warning: {src} not found and {dst} does not exist; "
            f"skipping vendor copy (the .typ import may not resolve).",
            file=sys.stderr,
        )
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def assemble_book(paths: list[Path]) -> str:
    """Concatenate several chapter .md files into one Typst document, each
    starting on a new page.  Image paths stay relative to the first file's
    directory, so the output must be written alongside it (see main)."""
    global _PAGE_BROKEN, _FENCE, _PFTAB_NAME, _ANSWERS_BUF
    _PAGE_BROKEN = False  # reset so the first heading of the book has no break
    _FENCE = None
    _PFTAB_NAME = ""
    _ANSWERS_BUF = []
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
