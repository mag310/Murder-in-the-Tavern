# Что ещё не готово

> Часть модуля «Убийство в таверне». Source of truth: `../../characters`, `locations/`, `organizations/`,
> `evidence.json`, `murder_matrix.json`, `flood_mechanic.json`, `nightly_beats.json`, `events.json`,
> `interrogations/`. Всё — канон; `null`/`needs_definition` в JSON = незаполнено.

## 8. Что ещё не готово (→ todo.md §26)

- **§26.2 Handouts:** `../../evidence-description.json` — 91/91 улик имеют `player_text` + `handout`. 2026-09-30.
- **§26.3 Игровые карты:** `..` содержит карты Westcrown/Cheliax/мост + `location_graph.mermaid`; нет
  player/GM map с легендой (без/с секретами).
- **§26.4 Инструменты мастера:** чек-лист улик, флоучарт, таймлайн-таблица, random tables; **quick ref — готово**
  (`06-quick-reference.md`, 2026-10-06).
- **§11 Opening / §15 behavior / §18–§19 win-lose/end states** — P0, не завершены.
  (§14 timeline — готово, см. `01-chronology.md §2.2`/`§2.3`.)
- **§6 PF2e-слой:** **stat blocks — готовы** (`../lore/stat-blocks.md`, 14 NPC + стражники); **DC/СЛ — готовы**
  (`locations/*.json.hidden[].check` + `observation`, `locations.schema.json`, 2026-10-06); skill challenges — ещё нет.

> Следующий шаг: §15 (behavior layer). §26.2 (handouts) — готово (`../../evidence-description.json`, 2026-09-30);
> §14 (timeline) — готово (`01-chronology.md`); §6 stat blocks + DC/СЛ — готовы (`stat-blocks.md`,
> `locations/*.json.hidden[].check`, 2026-10-06); §26.4 quick ref — готово (`06-quick-reference.md`).
> Не хватает человекочитаемой надстройки и игрового цикла.