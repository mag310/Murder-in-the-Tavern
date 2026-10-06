# Убийство в таверне — модуль для мастера (публикация)

Человекочитаемая надстройка над данными (source of truth: `../../characters`, `locations/`, `organizations/`,
`evidence.json`, `murder_matrix.json`, `flood_mechanic.json`, `nightly_beats.json`, `events.json`,
`interrogations/`). Всё — канон; `null`/`needs_definition` в JSON = незаполнено.

**Детектив, не боевой one-shot.** PF2e-механика: **stat blocks — в `../lore/stat-blocks.md`**; проверки/DC/
skill challenges — в todo. Здесь — нарратив и схема расследования.

## Содержание

| # | Файл                    | Тема                                                                                      |
|---|-------------------------|-------------------------------------------------------------------------------------------|
| 0 | `00-synopsis.md`        | Синопсис: что произошло, кто виноват, кто что скрывает                                    |
| 1 | `01-chronology.md`      | Хронология: предистория (event_001–021), главы 1–6, таймер потопа                         |
| 2 | `02-investigation.md`   | Схема расследования: d6-механика, матрицы убийства, улики                                 |
| 3 | `03-npcs.md`            | Мотивации и секреты NPC (6 главных + контекстные)                                         |
| 4 | `04-branching.md`       | Ветвление: что если игроки пойдут не туда, пути к остановке потопа, реакции NPC           |
| 5 | `05-endings.md`         | Финал: 4 концовки                                                                         |
| 6 | `06-quick-reference.md` | Быстрые ссылки                                                                            |
| 7 | `07-status.md`          | Что ещё не готово (→ todo.md §26)                                                         |
| — | `../lore/stat-blocks.md`        | PF2e-стат-блоки: 14 NPC + стражники/лейтенант/культист/контрабандист (Building Creatures) |

## Что есть в данных (source of truth)

- `../../events.json` — 33 события, 8 глав (timeline).
- `../../flood_mechanic.json` — таймер 24 ч, `water_rise` (затопление снизу вверх), 4 endings, 6 resolution_paths.
- `../../murder_matrix.json` — 6 матриц (жертва × possible_killers/required_evidence/false_leads/special_consequences).
- `../../characters` — 13 файлов (6 main_npc + контекстные + призраки) с `speech_profile`.
- `../../interrogations` — 6 файлов (допросы, L1–L4, delivery).
- `../../evidence.json` — 91 улик (роль: primary/secondary/false/accident). Описания + раздатки: `evidence-description.json`
  (91/91).
- `../lore/stat-blocks.md` — PF2e-стат-блоки всех NPC/комбатантов (AC/HP/спасброски/атаки, по таблице Building Creatures).

## Что ещё не готово

- **§26.2 Handouts:** `../../evidence-description.json` — 91/91 улик имеют `player_text` + `handout`. 2026-09-30.
- **§26.3 Игровые карты:** `..` содержит карты Westcrown/Cheliax/мост + `location_graph.mermaid`; нет
  player/GM map с легендой (без/с секретами).
- **§26.4 Инструменты мастера:** чек-лист улик, флоучарт, таймлайн-таблица, random tables, quick ref.
- **§11 Opening / §15 behavior / §18–§19 win-lose/end states** — P0, не завершены. (§14 timeline — готово, см.
  `01-chronology.md §2.2`/`§2.3`.)
- **§6 PF2e-слой:** **stat blocks — готовы** (`../lore/stat-blocks.md`, 14 NPC + стражники); DC и skill challenges — ещё нет.
