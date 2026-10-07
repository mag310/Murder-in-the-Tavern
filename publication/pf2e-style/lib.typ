#import "style/formatting.typ": *

// Pulled from https://github.com/typst/typst/issues/2196
#let to-string(it) = {
  if type(it) == str {
    it
  } else if type(it) != content {
    str(it)
  } else if it.has("text") {
    it.text
  } else if it.has("children") {
    it.children.map(to-string).join()
  } else if it.has("body") {
    to-string(it.body)
  } else if it == [ ] {
    " "
  }
}

#let roll-result(it) = {
  let output = false
  if to-string(it).starts-with("Critical Success") {output = true}
  else if to-string(it).starts-with("Success") {output = true}
  else if to-string(it).starts-with("Failure") {output = true}
  else if to-string(it).starts-with("Critical Failure") {output = true}
  else if to-string(it).starts-with("Heightened (") {output = true}
  return output
}

#let pftraits(traits) = {
  // NOTE: vendored local fix for Typst 0.15.x — a single-element `[x]` is not
  // iterable, so we normalise the traits to a tuple (which is iterable) and
  // loop with `for`.  This replaces the original `.map(...)` that failed on
  // single-element content in this Typst version.
  let base = if type(traits) in (array, list) { traits } else { (traits,) }
  for trait in base [
#let style = if trait == "tiny" or trait == "small" or trait == "medium" or trait == "large" {
      rgb("#3a7a58") // Size Green
    } else if trait == "uncommon" {
        orange
    } else if trait == "rare" {
        navy
    } else if trait == "unique" {
        rgb("#871F78") // Dark Purple
    } else {
    colors.pfmaroon
  }
#box(
      fill: style,
    stroke: (
      left: colors.pfyellow + 2pt,
      right: colors.pfyellow + 2pt,
      top: colors.pfyellow + 1pt,
      bottom: colors.pfyellow + 1pt,
    ),
      inset: 4pt
    )[#text(weight: "semibold", size: .8em, fill: white)[#upper[#trait]]]
]}

// Action Icons
#let A = (
  box(image("style/action-icons/single.svg", height: 1em))
)
#let AA = (
  box(image("style/action-icons/double.svg", height: 1em))
)
#let AAA = (
  box(image("style/action-icons/triple.svg", height: 1em))
)
#let R = (
  box(image("style/action-icons/reaction.svg", height: 1em))
)
#let F = (
  box(image("style/action-icons/free.svg", height: 1em))
)

#let box-top(info) = [
  #text(size: 1.3em, weight: "extrabold")[#align(center)[#info\ ]]
]

#let pftab(name, columns: (1fr, 4fr), breakable: false, ..contents) = [
  #v(1em)
  #block(breakable: breakable)[
  *#smallcaps(text(size: 1.3em)[#upper(name)])*
  #v(-.5em)
  #table(
  columns: columns,
  align: (col, row) =>
   if col == 0 { center }
    else { center },
  fill: (col, row) => if row == 0 {rgb("002a16") } else if calc.odd(row+1) { colors.pfwhite } else { colors.otherRow },
  inset: 5pt,
  stroke: none,
  // align: horizon,
  ..contents
  )
  #v(1em)
]]

#let chap-header(num, title, desc) = place(
  center + top,
  // dx: 55%,
  dy: -5%,
  scope: "parent",
  float: true,
  clearance: -0.5em,
)[
  #set text(fill: colors.pfgreen)
  #layout(size => {
    let content = text(weight: "extrabold")[
      #text(1.5em, font: "Taroca")[#upper(num)] \ 
      #text(2em, font: "Taroca")[#upper(title)] \ 
      #text(1.2em, style: "italic")[#desc]
    ]
    
    block(
      fill: rgb("#f4eee0"),
      stroke: (
        bottom: 3pt + rgb("#664200"),
        rest: none,
      ),
      width: 115%,
      inset: 1em,
      outset: 1em,
      align(center, content)
      // outset: (x: 200%, y: (m.height / 2)),
    )
  })
]

#let note(info) = [
  #v(1em)
  #box(
    fill: rgb("#e2d7d3"),
    inset: 7pt,
    // outset: 2pt,
  )[
    #show heading: it => align(center)[#it] 
    #info
  ]
]

// A titled note: a bold title lead line above the note body, inside the same
// tan box as #note.  The generator emits this for `::: note[Title]`.
#let note-titled(title, info) = [
  #v(1em)
  #box(
    fill: rgb("#e2d7d3"),
    inset: 7pt,
  )[
    #show heading: it => align(center)[#it]
    #text(weight: "bold")[#title]
    #linebreak()
    #info
  ]
]

#let attention(content) = [
  #v(1em)
  #box(
    fill: rgb("#eadcb7"),
    stroke: (1pt + black),
    inset: 4pt,
  )[
    #show heading: it => align(center)[#it] 
    #content
  ]
]

#let aloud(content) = [
  #v(.5em)
  #line(stroke: 1pt + colors.pfbrown, length: 100%)
  #text(fill: colors.pfbrown)[#content]
  #line(stroke: 1pt + colors.pfbrown, length: 100%)
  #v(.5em)
]

// A titled read-aloud: a bold title lead line above the read-aloud body, then
// the same brown box as #aloud.  The generator emits this for `::: aloud[Title]`.
#let aloud-titled(title, content) = [
  #v(.5em)
  #line(stroke: 1pt + colors.pfbrown, length: 100%)
  #text(fill: colors.pfbrown, weight: "bold")[#title]
  #linebreak()
  #text(fill: colors.pfbrown)[#content]
  #line(stroke: 1pt + colors.pfbrown, length: 100%)
  #v(.5em)
]

#let spell(spl) = [
  #v(1em)
    #set par(spacing: .6em, first-line-indent: 0em) // hanging-indent: 1em)
    #let creature_header(body) = {
      box(
        text(weight: "extrabold",size: 1.4em, stretch: 50%)[#upper(spl.name)]
      )
      h(1fr)
      sym.wj
      box(text(weight: "extrabold",size: 1.4em, stretch: 50%)[#upper(body)])
    }
    #creature_header[#spl.type]
    #line(stroke: 1pt, length: 100%)
    #pftraits(spl.traits)
  
  #for req in spl.reqs {
    par(hanging-indent: 1em)[#req\ ]
  }
  #line(stroke: 1pt, length: 100%)
  #for effect in spl.effect {
  if to-string(effect).starts-with("•") {
    par(hanging-indent: 1.7em, first-line-indent: 1em)[#effect]
  } else if roll-result(effect){
    par(hanging-indent: 1em, first-line-indent: 0em)[#effect]
  } else if effect == [---] or effect == [line] {line(stroke: 1pt, length: 100%)
  } else {par(hanging-indent: 0em, first-line-indent: 1em)[#effect]}}
]

#let feat(feat) = [
  #v(1em)
    #set par(spacing: .6em, first-line-indent: 0em) // hanging-indent: 1em)
    #set text(size: 10pt) 
    #let creature_header(body) = {
      box(
        text(weight: "extrabold", size: 1.4em, stretch: 50%)[#upper(feat.name)]
      )
      h(1fr)
      sym.wj
      box(text(weight: "extrabold",size: 1.4em, stretch: 50%)[FEAT #body])
    }
    #creature_header[#feat.level]
    #line(stroke: 1pt, length: 100%)
  #pftraits(feat.traits)
  
  #for feat in feat.reqs {
    par(hanging-indent: 1em)[#feat\ ]
  }
  #if feat.reqs != () {
    line(stroke: 1pt, length: 100%)
  }
  #for effect in feat.effect {
  if roll-result(effect) {
    par(hanging-indent: 1em)[#effect]
  } else {
  par(hanging-indent: 0pt, first-line-indent: 1em)[#effect]}}
  #if feat.special != [] {
    line(stroke: 1pt, length: 100%)
    par(hanging-indent: 1em)[#feat.special\ ]
  }
]

#let encounter(comp) = [
  #v(1em)
    #set par(spacing: .6em, first-line-indent: 0em) // hanging-indent: 1em)
    #let creature_header(body) = {
      box(
        text(weight: "extrabold", size: 1.3em, stretch: 50%)[#upper(comp.name)]
      )
      h(1fr)
      sym.wj
      box(text(weight: "extrabold",size: 1.3em, stretch: 50%)[#upper(comp.type)])
    }
    #creature_header[]
    #line(stroke: 1pt, length: 100%)
  #pftraits(comp.traits)
  #for entry in (comp.details) {
  if entry == [---] or entry == [line] {line(stroke: 1pt, length: 100%); continue}
  if roll-result(entry) {par(hanging-indent: 1em)[#entry]; continue}
  if comp.type == [Complication] or comp.type == [Opportunities] or comp.type == [] or comp.type == [Obstacle]  {par(hanging-indent: 0em)[#entry]; continue}
  if comp.type == [Background] {par(hanging-indent: 0em, first-line-indent: 1em)[#entry]; continue}
  // if entry.has(<r>) {entry;continue}
    par(hanging-indent: 1em)[#entry] 
  }
    // #line(stroke: 1pt, length: 100%)
    // #comp.trigger
    // #line(stroke: 1pt, length: 100%)
    // #comp.effect
]

// ============================================================
// Цвета уровней (левая колонка)
// ============================================================
#let att-colors = (
  hostile:     rgb("5a1a1a"),
  unfriendly:  rgb("7a3a1a"),
  indifferent: rgb("5a5a2a"),
  friendly:    rgb("2a5a2a"),
  helpful:     rgb("1a4a3a"),
  very_hard:   rgb("5a1a1a"),
  easy:        rgb("7a3a1a"),
  medium:      rgb("5a5a2a"),
  very_easy:   rgb("1a4a3a"),
  // check-уровни исхода (тот же набор цветов по значимости):
  critical_success:   rgb("1a4a3a"),
  success:            rgb("2a5a2a"),
  failure:            rgb("7a3a1a"),
  critical_failure:   rgb("5a1a1a"),
)

// ============================================================
// Метки уровней
// ============================================================
#let att-labels = (
  hostile:     "Враждебный (-2)",
  unfriendly:  "Недружелюбный (-1)",
  indifferent: "Безразличный (0)",
  friendly:    "Дружелюбный (+1)",
  helpful:     "Полезный (+2)",
  very_hard:   "Не доверяет (-2)",
  easy:        "Осторожный (-1)",
  medium:      "Доверяет (+1)",
  very_easy:   "Полностью доверяет (+2)",
  // check-уровни исхода:
  critical_success:   "Крит. успех",
  success:            "Успех",
  failure:            "Провал",
  critical_failure:   "Крит. провал",
)

// ============================================================
// answers-group
// ============================================================
#let answers-group(npc, ..blocks) = {
  heading(level: 4)[#npc]
  for b in blocks.pos() {
    b
  }
}

// ============================================================
// answers
// ------------------------------------------------------------
// Строка 0 — заголовок (colspan=2): npc (курсив) + q (жирный),
//            фон pfgreen, текст pfwhite.
// Строки 1..N — уровни:
//   левая ячейка: метка, фон = att-colors.at(key), текст белый;
//   правая ячейка: ответ, без заливки.
// ============================================================
#let answers(
  npc: none,
  q: none,
  hostile: none,
  unfriendly: none,
  indifferent: none,
  friendly: none,
  helpful: none,
  very_hard: none,
  easy: none,
  medium: none,
  very_easy: none,
) = {
  let pairs = (
    (key: "hostile",     body: hostile),
    (key: "unfriendly",  body: unfriendly),
    (key: "indifferent", body: indifferent),
    (key: "friendly",    body: friendly),
    (key: "helpful",     body: helpful),
    (key: "very_hard",   body: very_hard),
    (key: "easy",        body: easy),
    (key: "medium",      body: medium),
    (key: "very_easy",   body: very_easy),
  ).filter(p => p.body != none)

  // --- Заголовок: одна ячейка на две колонки ---
  let header = table.cell(
    colspan: 2,
    fill: colors.pfgreen,
    inset: (x: 6pt, y: 5pt),
    align: left + horizon,
  )[
    #if npc != none {
      text(fill: colors.pfwhite, size: 0.9em, style: "italic")[#npc]
      if q != none { h(0.5em) }
    }
    #if q != none {
      text(fill: colors.pfwhite, weight: "bold")[#q]
    }
  ]

  // --- Строки уровней ---
  let rows = pairs.map(p => (
    table.cell(
      fill: att-colors.at(p.key),
      inset: (x: 6pt, y: 4pt),
      align: left,
    )[
      #text(fill: colors.pfwhite, weight: "bold")[#att-labels.at(p.key)]
    ],
    table.cell(
      inset: (x: 6pt, y: 4pt),
      align: left,
    )[#p.body],
  )).flatten()

  block(breakable: true)[
    #v(0.6em)
    #table(
      columns: (auto, 1fr),
      stroke: none,
      inset: 0pt,
      fill: none,
      header,
      ..rows,
    )
    #v(0.6em)
  ]
}

// ============================================================
// check / check-group
// ------------------------------------------------------------
// #check-group(intro, ..blocks) — групповая обёртка, по аналогии с
// #answers-group: заголовок (intro, level 4) + список #check.
//
// #check(skill, dc, critical_success, success, failure, critical_failure)
// — одна проверка с 4 уровнями исхода (крит. успех / успех / провал /
// крит. провал), отрисованная как #answers (таблица с цветными метками
// исхода слева и текстом справа; незаданные уровни пропускаются).
// ============================================================
#let check-group(intro, ..blocks) = {
  heading(level: 4)[#intro]
  for b in blocks.pos() {
    b
  }
}

#let check(
  skill,
  dc,
  critical_success: none,
  success: none,
  failure: none,
  critical_failure: none,
) = {
  // Порядок строк: от самого лучшего исхода к худшему.
  let pairs = (
    (key: "critical_success",   body: critical_success),
    (key: "success",            body: success),
    (key: "failure",            body: failure),
    (key: "critical_failure",   body: critical_failure),
  ).filter(p => p.body != none)

  // --- Заголовок: одна двойная ячейка (colspan=2) с двумя блоками внутри ---
  // `skill` and `dc` arrive as positional `content` (e.g. `[Природа]`,
  // `[15]`), so they are inserted directly.  The header is a single cell that
  // spans both columns (colspan: 2); inside it two blocks sit side by side:
  // the skill on the left and "DC #dc" on the right.  When no DC was given the
  // generator passes an empty `[]`, so only the skill block is shown.
  // The DC block: a numeric DC is prefixed with "DC" (e.g. "DC 15"); a
  // non-numeric value (e.g. "50 зм") is shown verbatim with no "DC" prefix.
  let dc-str = to-string(dc)
  // A value is numeric when, after keeping only digit/dot characters, the
  // result equals the trimmed value (so "15" / "15.5" are numeric, while
  // "50 зм" / "крит. успех" are not).
  let is-numeric = dc-str != "" and dc-str.trim().split("").filter(
    c => c in "0123456789.",
  ).join() == dc-str.trim()
  let dc-block = if dc-str != "" {
    if is-numeric {
      text(fill: colors.pfwhite, weight: "bold")[DC #dc]
    } else {
      text(fill: colors.pfwhite, weight: "bold")[#dc]
    }
  } else {
    []
  }
  // A single double cell (colspan: 2) holding two blocks on one line: the
  // skill on the left and the DC value pushed to the right by h(1fr).  The
  // header is one line tall (a table cell does not grow to two rows), so the
  // two blocks stay on the same line.
  let header = table.cell(
    colspan: 2,
    fill: colors.pfgreen,
    inset: (x: 6pt, y: 5pt),
    align: left + horizon,
  )[
    #text(fill: colors.pfwhite, weight: "bold")[#skill]
    #if dc-str != "" { h(1fr) }
    #dc-block
  ]

  // --- Строки исходов ---
  let rows = pairs.map(p => (
    table.cell(
      fill: att-colors.at(p.key),
      inset: (x: 6pt, y: 4pt),
      align: left,
    )[
      #text(fill: colors.pfwhite, weight: "bold")[#att-labels.at(p.key)]
    ],
    table.cell(
      inset: (x: 6pt, y: 4pt),
      align: left,
    )[#p.body],
  )).flatten()

  block(breakable: true)[
    #v(0.6em)
    #table(
      columns: (1fr, 3fr),
      stroke: none,
      inset: 0pt,
      fill: none,
      header,
      ..rows,
    )
    #v(0.6em)
  ]
}