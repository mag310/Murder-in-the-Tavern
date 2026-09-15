# Убийство в таверне — модуль для мастера (публикация)

Человекочитаемая надстройка над данными (source of truth: `characters/`, `locations/`, `organizations/`,
`evidence.json`, `murder_matrix.json`, `flood_mechanic.json`, `nightly_beats.json`, `events.json`,
`interrogations/`). Всё — канон; `null`/`needs_definition` в JSON = незаполнено.

**Детектив, не боевой one-shot.** PF2e-механика (проверки, DC, таймер) — в todo. Здесь — нарратив и
схема расследования.

## Содержание

| # | Файл                    | Тема                                                                            |
|---|-------------------------|---------------------------------------------------------------------------------|
| 0 | `00-synopsis.md`        | Синопсис: что произошло, кто виноват, кто что скрывает                          |
| 1 | `01-chronology.md`      | Хронология: предистория (event_001–021), главы 1–6, таймер потопа               |
| 2 | `02-investigation.md`   | Схема расследования: d6-механика, матрицы убийства, улики                       |
| 3 | `03-npcs.md`            | Мотивации и секреты NPC (6 главных + контекстные)                               |
| 4 | `04-branching.md`       | Ветвление: что если игроки пойдут не туда, пути к остановке потопа, реакции NPC |
| 5 | `05-endings.md`         | Финал: 4 концовки                                                               |
| 6 | `06-quick-reference.md` | Быстрые ссылки                                                                  |
| 7 | `07-status.md`          | Что ещё не готово (→ todo.md §26)                                               |

## Что есть в данных (source of truth)

- `events.json` — 30 событий, 7 глав (timeline).
- `flood_mechanic.json` — таймер 24 ч, `water_rise` (затопление снизу вверх), 4 endings, 6 resolution_paths.
- `murder_matrix.json` — 6 матриц (жертва × possible_killers/required_evidence/false_leads/special_consequences).
- `characters/` — 13 файлов (6 main_npc + контекстные + призраки) с `speech_profile`.
- `interrogations/` — 6 файлов (допросы, L1–L4, delivery).
- `evidence.json` — 75 улик (роль: primary/secondary/false/accident; `content` сейчас пуст — §2 todo / §26.2).

## Что ещё не готово

- **§26.2 Handouts:** `evidence.content` пуст (0/75) — нужно наполнить и сделать читаемым в печати.
- **§26.3 Игровые карты:** есть только логический граф `location_graph.mermaid`; нет player/GM map.
- **§26.4 Инструменты мастера:** чек-лист улик, флоучарт, таймлайн-таблица, random tables, quick ref.
- **§11 Opening / §14 Timeline / §15 behavior / §18–§19 win-lose/end states** — P0, не завершены.
- **§6 PF2e-слой:** stat blocks, DC, skill challenges — не добавлены (текущий модуль — нарратив).
