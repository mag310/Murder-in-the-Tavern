#!/usr/bin/env python3
"""Generate interrogation data from the new *-ansvers.md files.

For each character:
  * extract L1..L5 dialogue tables (reusing extract_dialogue),
  * clean text (strip [cite:..], <br>, **bold, collapse whitespace),
  * dedup by question text (keep the richest answer set),
  * assign block IDs (A1, B1, ...),
  * emit:
      1) interrogations/{character_id}.json  (schema-compliant)
      2) a `::: answers` block file  ->  generators/_answers_{character_id}.md
      3) a masters-book "Диалог" snippet -> generators/_masters_{character_id}.md

The detective JSON is updated by MERGING (existing base_questions kept; new
questions appended only if the question text is new).
"""
import json
import re
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parent))
from extract_dialogue import extract  # noqa: E402

ROOT = Path(r"C:\Users\User\Murder-in-the-Tavern")

# character_id -> (md file, name, role, attitude, base_dc, candor, reliability,
#                  npc_label_for_answers, status)
CHARS = {
    "duxotar": {
        "md": "interrogations/duxotar-ansvers.md",
        "name": "Ильтус Мартис",
        "role": "Дуксотар",
        "attitude": "unfriendly",
        "base_dc": "hard",
        "candor": "unfriendly",
        "reliability": "mixed",
        "npc_label": "Дуксотар Ильтус Мартис",
        "status": "main_npc",
    },
    "capitan": {
        "md": "interrogations/capitan-ansvers.md",
        "name": "Алессандро Маретти",
        "role": "Капитан «Чёрной Сирены»",
        "attitude": "indifferent",
        "base_dc": "medium",
        "candor": "indifferent",
        "reliability": "reliable",
        "npc_label": "Капитан Алессандро Маретти",
        "status": "main_npc",
    },
    "doctor_assistant": {
        "md": "interrogations/doctor_assistant-ansvers.md",
        "name": "Тобиа Бандини",
        "role": "Ассистент Доктора",
        "attitude": "indifferent",
        "base_dc": "medium",
        "candor": "indifferent",
        "reliability": "mixed",
        "npc_label": "Тобиа Бандини — Ассистент Доктора",
        "status": "main_npc",
    },
    "vassindio": {
        "md": "interrogations/vassindio_drovenge-ansvers.md",
        "name": "Вассиндио Дровендж",
        "role": "Патриарх Совета Воров",
        "attitude": "unfriendly",
        "base_dc": "hard",
        "candor": "unfriendly",
        "reliability": "mixed",
        "npc_label": "Вассиндио Дровендж — Патриарх Совета Воров",
        "status": "main_npc",
    },
    "detective": {
        "md": "interrogations/detective-ansvers.md",
        "name": "Джакомо Раньери",
        "role": "Детектив",
        "attitude": "unfriendly",
        "base_dc": "hard",
        "candor": "unfriendly",
        "reliability": "mixed",
        "npc_label": "Джакомо Раньери — Детектив",
        "status": "main_npc",
    },
}

LEVELS = ["hostile", "unfriendly", "indifferent", "friendly", "helpful"]


def clean(s: str) -> str:
    """Strip [cite:..], <br>, **bold markers, collapse whitespace."""
    if not s:
        return ""
    s = re.sub(r"\[cite:\s*[^]]*\]", "", s, flags=re.I)
    s = re.sub(r"<br\s*/?>", " ", s)
    s = s.replace("**", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _norm(s: str) -> str:
    """Normalization key for dedup/merge (lowercased, collapsed)."""
    return re.sub(r"\s+", " ", clean(s).lower()).strip()


def _id_at(i: int) -> str:
    """Block ID for position i (0-based): A1, A2, ... A10, B1, ..."""
    block = i // 10
    idx = i % 10 + 1
    letter = BLOCK_LETTERS[block] if block < len(BLOCK_LETTERS) else "A"
    return letter + str(idx)


def _next_id(used: set) -> str:
    """Find the next unused block ID (A1, A2, ... B1, ...)."""
    for i in range(2000):
        bid = _id_at(i)
        if bid not in used:
            used.add(bid)
            return bid
    return "Z99"


def dedup(recs):
    """Dedup by question text; keep the entry with the most non-empty levels
    (ties: longest total answer chars)."""
    seen = {}
    for r in recs:
        q = clean(r["question"])
        if not q:
            continue
        key = re.sub(r"\s+", " ", q.lower()).strip()
        if not key:
            continue
        levels = sum(1 for lvl in LEVELS if clean(r.get(lvl, "")))
        total = sum(len(clean(r.get(lvl, ""))) for lvl in LEVELS)
        prev = seen.get(key)
        if prev is None or (levels, total) > prev[0]:
            seen[key] = ((levels, total), q, r)
    # preserve original order, deduped
    out = []
    used = set()
    for r in recs:
        q = clean(r["question"])
        if not q:
            continue
        key = re.sub(r"\s+", " ", q.lower()).strip()
        if key in used:
            continue
        used.add(key)
        out.append(seen[key][2])
    return out


BLOCK_LETTERS = "ABCDEFGHJKLMNPRSTUVWXY"  # skip I and Q is fine but keep simple


def block_ids(n: int) -> list[str]:
    """A1, A2, ... A10, B1, ... (10 per block)."""
    ids = []
    for i in range(n):
        block = i // 10
        idx = i % 10 + 1
        letter = BLOCK_LETTERS[block] if block < len(BLOCK_LETTERS) else "A"
        ids.append(letter + str(idx))
    return ids


def make_json(cid: str, recs, cfg) -> dict:
    deduped = dedup(recs)
    ids = block_ids(len(deduped))
    base = {}
    for i, r in enumerate(deduped):
        bid = ids[i]
        entry = {"q": clean(r["question"])}
        for lvl in LEVELS:
            a = clean(r.get(lvl, ""))
            if a:
                entry[lvl] = a
        base[bid] = entry
    data = {
        "character_id": cid,
        "name": cfg["name"],
        "role": cfg["role"],
        "status": cfg["status"],
        "attitude": cfg["attitude"],
        "base_dc": cfg["base_dc"],
        "default_reliability": cfg["reliability"],
        "candor_level": cfg["candor"],
        "base_questions": base,
        "scenarios": [],
    }
    return data


def make_answers_md(cid: str, recs, cfg) -> str:
    deduped = dedup(recs)
    out = ["::: answers", cfg["npc_label"], ""]
    for r in deduped:
        q = clean(r["question"])
        if not q:
            continue
        out.append("**Q:** " + q)
        for lvl in LEVELS:
            a = clean(r.get(lvl, ""))
            if a:
                out.append(f"{lvl}: {a}")
        out.append("")
    out.append(":::")
    return "\n".join(out).rstrip() + "\n"


def make_masters_md(cid: str, recs, cfg) -> str:
    deduped = dedup(recs)
    out = []
    out.append("#### Диалог: допрос %s" % cfg["npc_label"])
    out.append("")
    out.append(
        "> Полные ответы по 5 уровням откровенности (`candor_level` = `attitude`, "
        "стартовое `%s`, DC `%s`). Источник: `interrogations/%s.json`, "
        "`../interrogations/%s-ansvers.md`."
        % (cfg["attitude"], cfg["base_dc"], cid, cfg["md"].split("/")[-1])
    )
    out.append("")
    for r in deduped:
        q = clean(r["question"])
        if not q:
            continue
        out.append("**Q:** " + q)
        for lvl in LEVELS:
            a = clean(r.get(lvl, ""))
            if a:
                out.append("    - **%s:** %s" % (lvl.capitalize(), a))
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main():
    for cid, cfg in CHARS.items():
        md_path = ROOT / cfg["md"]
        recs = extract(str(md_path))
        deduped = dedup(recs)
        print("%-16s %3d raw -> %3d unique" % (cid, len(recs), len(deduped)))
        # JSON
        data = make_json(cid, recs, cfg)
        json_path = ROOT / "interrogations" / (cid + ".json")
        if json_path.exists() and cid == "detective":
            # MERGE: keep existing base_questions + scenarios; append new
            # questions (by normalized question text) to base_questions.
            old = json.loads(json_path.read_text(encoding="utf-8"))
            existing = set()
            for k, v in old.get("base_questions", {}).items():
                existing.add(_norm(v.get("q", "")))
            for s in old.get("scenarios", []):
                for v in s.get("questions", {}).values():
                    if isinstance(v, dict):
                        existing.add(_norm(v.get("q", "")))
            used_ids = set(old.get("base_questions", {}).keys())
            next_id = len(used_ids)
            added = 0
            for r in deduped:
                q = clean(r["question"])
                if not q or _norm(q) in existing:
                    continue
                existing.add(_norm(q))
                bid = _next_id(used_ids)
                entry = {"q": q}
                for lvl in LEVELS:
                    a = clean(r.get(lvl, ""))
                    if a:
                        entry[lvl] = a
                old["base_questions"][bid] = entry
                added += 1
            json_path.write_text(
                json.dumps(old, ensure_ascii=False, indent=4) + "\n",
                encoding="utf-8",
            )
            print("   detective.json merged: +%d new base_questions" % added)
            # still emit answers/masters snippets for reference
        else:
            json_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=4) + "\n",
                encoding="utf-8",
            )
        # answers md
        ans_path = ROOT / "generators" / ("_answers_" + cid + ".md")
        ans_path.write_text(make_answers_md(cid, recs, cfg), encoding="utf-8")
        # masters md
        m_path = ROOT / "generators" / ("_masters_" + cid + ".md")
        m_path.write_text(make_masters_md(cid, recs, cfg), encoding="utf-8")
        print("   wrote %s.json, _answers_%s.md, _masters_%s.md"
              % (cid, cid, cid))


if __name__ == "__main__":
    main()
