#!/usr/bin/env python3
"""Extract dialogue tables from a new interrogation .md file into a structured
list of {npc, heading, question, {hostile,unfriendly,indifferent,friendly,helpful}}.

Reuses the table-detection logic from convert_dialogue_tables.py.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from convert_dialogue_tables import (  # noqa: E402
    is_dialogue_table,
    level_key_for,
    parse_table_rows,
    find_table_span,
    nearest_heading_before,
)

# order of levels as they appear in a 5-col table
LEVELS = ["hostile", "unfriendly", "indifferent", "friendly", "helpful"]


def extract(md_path: str):
    txt = open(md_path, encoding="utf-8").read()
    lines = txt.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        if ln.strip().startswith("|") and "Вопрос" in ln:
            j = find_table_span(lines, i)
            block = lines[i:j]
            rows = parse_table_rows(block)
            if rows:
                header = rows[0]
                data = rows[1:]
                if is_dialogue_table(header) and data:
                    heading = nearest_heading_before(lines, i)
                    # question col
                    q_col = 0
                    for k, c in enumerate(header):
                        if c.strip().lower().replace("**", "").strip().startswith("вопрос"):
                            q_col = k
                            break
                    # level cols
                    col_keys = []
                    for k, c in enumerate(header):
                        if k == q_col:
                            continue
                        key = level_key_for(c)
                        if key:
                            col_keys.append((k, key))
                    for row in data:
                        if not row or q_col >= len(row):
                            continue
                        q = row[q_col].strip().replace("**", "").strip()
                        q = re.sub(r"\s+", " ", q)
                        if not q:
                            continue
                        rec = {"heading": heading, "question": q}
                        for ci, key in col_keys:
                            if ci < len(row):
                                a = row[ci].strip()
                                if a in ("", "—", "-"):
                                    continue
                                a = re.sub(r"\s+", " ", a).strip()
                                rec[key] = a
                        # also record raw answers in table order (for tables
                        # that mix columns not matching the 5-level set)
                        out.append(rec)
            i = j
            continue
        i += 1
    return out


if __name__ == "__main__":
    import json
    target = sys.argv[1] if len(sys.argv) > 1 else "interrogations/duxotar-ansvers.md"
    recs = extract(target)
    print("extracted %d questions from %s" % (len(recs), target))
    # dump
    op = "generators/_extract_" + Path(target).stem + ".json"
    open(op, "w", encoding="utf-8").write(json.dumps(recs, ensure_ascii=False, indent=2))
    print("wrote", op)
