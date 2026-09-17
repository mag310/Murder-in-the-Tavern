from PIL import Image, ImageDraw

# Spritesheet specifications — top-down (plan) view of beds.
# Cells are 64x64. Double/2-story beds are 64x128 (2 rows); horizontal beds
# are 128x64 (2 cols). The 8x8 canvas packs every combination cleanly.
CELL = 64
COLS = 8
ROWS = 8
WIDTH = CELL * COLS   # 512 px
HEIGHT = CELL * ROWS  # 512 px

img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)


def shade(c, f):
    """Multiply an RGB tuple by a factor (clip to 0..255)."""
    return tuple(max(0, min(255, int(v * f))) for v in c)


# Palettes (Dark Fantasy Style) — two materials, each with a light and a
# dark tone. Wood = warm brown; Iron = cold slate/steel.
W = {
    "base": (118, 86, 56),
    "dark": (74, 53, 34),
    "hi": (156, 122, 80),
}
M = {
    "base": (96, 101, 112),
    "dark": (52, 56, 64),
    "hi": (150, 156, 168),
}
# Bedding colours: (cloth, pillow).
CLOTH = {
    "wood": ((126, 52, 52), (196, 176, 150)),   # deep red cloth + pale pillow
    "iron": ((86, 82, 96), (170, 176, 190)),    # cold grey-blue cloth + pale pillow
}


def plan_frame(x0, y0, w, h, pal, cloth_key, head="top", ladder=None):
    """Draw a bed as a top-down (plan) view inside the rect (x0,y0,w,h).
    head: which short edge holds the pillow ("top"/"bottom" for a vertical
    bed, "left"/"right" for a horizontal bed).
    ladder: optional (lx, ly, lw, lh) rect for a plan-view ladder (2-story)."""
    base = pal
    cloth, pillow = CLOTH[cloth_key]
    # soft drop shadow
    draw.rectangle([x0 + 2, y0 + 2, x0 + w + 2, y0 + h + 2], fill=(0, 0, 0, 60))
    # frame (full outline)
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill=base["dark"])
    draw.rectangle([x0, y0, x0 + w, y0 + 3], fill=base["hi"])
    draw.rectangle([x0 + 3, y0, x0 + 3, y0 + h], fill=base["hi"])
    draw.rectangle([x0, y0 + h - 3, x0 + w, y0 + h], fill=base["dark"])
    draw.rectangle([x0 + w - 3, y0, x0 + w - 3, y0 + h], fill=base["hi"])
    # inner wood border
    draw.rectangle([x0 + 3, y0 + 3, x0 + w - 3, y0 + h - 3], outline=base["base"], width=2)
    # bedding (blanket) inside the frame
    bx = x0 + 6
    by = y0 + 6
    bw = w - 12
    bh = h - 12
    draw.rectangle([bx, by, bx + bw, by + bh], fill=shade(cloth, 0.9))
    # blanket highlight (top-left sheen)
    draw.rectangle([bx, by, bx + bw, by + 3], fill=shade(cloth, 1.15))
    draw.rectangle([bx, by, bx + 3, by + bh], fill=shade(cloth, 1.1))
    # blanket shadow (bottom-right)
    draw.rectangle([bx, by + bh - 3, bx + bw, by + bh], fill=shade(cloth, 0.65))
    draw.rectangle([bx + bw - 3, by, bx + bw, by + bh], fill=shade(cloth, 0.65))
    # a fold line across the blanket (towards the foot)
    if head in ("top", "bottom"):
        fold_y = by + bh // 2
        draw.line([bx, fold_y, bx + bw, fold_y], fill=shade(cloth, 1.2), width=1)
    else:
        fold_x = bx + bw // 2
        draw.line([fold_x, by, fold_x, by + bh], fill=shade(cloth, 1.2), width=1)
    # pillow at the head
    if head == "top":
        pw, ph = bw - 10, 12
        px = bx + 5
        py = by + 3
    elif head == "bottom":
        pw, ph = bw - 10, 12
        px = bx + 5
        py = by + bh - 15
    elif head == "left":
        pw, ph = 12, bh - 10
        px = bx + 3
        py = by + 5
    else:  # right
        pw, ph = 12, bh - 10
        px = bx + bw - 15
        py = by + 5
    draw.ellipse([px, py, px + pw, py + ph], fill=shade(pillow, 0.95))
    draw.ellipse([px + 1, py + 1, px + pw - 1, py + ph - 1], fill=shade(pillow, 1.15))
    # pillow highlight
    draw.ellipse([px + 2, py + 2, px + pw - 6, py + ph - 8], fill=shade(pillow, 1.3))
    # ladder (plan view) for 2-story bunks
    if ladder:
        lx, ly, lw, lh = ladder
        draw.rectangle([lx, ly, lx + lw, ly + lh], fill=base["dark"])
        draw.rectangle([lx, ly, lx + 3, ly + lh], fill=base["base"])
        draw.rectangle([lx + lw - 3, ly, lx + lw, ly + lh], fill=base["base"])
        for rung in range(ly + 5, ly + lh - 2, 10):
            draw.rectangle([lx, rung, lx + lw, rung + 3], fill=base["base"])
        # ladder rungs highlight
        draw.rectangle([lx + 1, ly + 1, lx + lw - 1, ly + 2], fill=base["hi"])


def draw_single(x0, y0, pal, cloth_key):
    """Single bed in a 64x64 cell, plan view (head at top)."""
    w, h = 48, 56
    fx, fy = x0 + 8, y0 + 4
    plan_frame(fx, fy, w, h, pal, cloth_key, head="top")


def draw_double(x0, y0, pal, cloth_key):
    """2-story bunk bed in a 64x128 cell, plan view: two beds stacked along
    the length axis with a ladder between them."""
    base = pal
    w = 48
    # upper bunk (top half)
    plan_frame(x0 + 8, y0 + 4, w, 56, pal, cloth_key, head="top")
    # lower bunk (bottom half)
    plan_frame(x0 + 8, y0 + 68, w, 56, pal, cloth_key, head="bottom")
    # ladder between the two bunks, on the right side (plan view)
    lx, ly = x0 + 8 + w + 4, y0 + 40
    lw, lh = 10, 44
    draw.rectangle([lx, ly, lx + lw, ly + lh], fill=base["dark"])
    draw.rectangle([lx, ly, lx + 3, ly + lh], fill=base["base"])
    draw.rectangle([lx + lw - 3, ly, lx + lw, ly + lh], fill=base["base"])
    for rung in range(ly + 5, ly + lh - 2, 10):
        draw.rectangle([lx, rung, lx + lw, rung + 3], fill=base["base"])
    draw.rectangle([lx + 1, ly + 1, lx + lw - 1, ly + 2], fill=base["hi"])


def draw_horizontal(x0, y0, pal, cloth_key, double=False):
    """Horizontal bed(s) in a 128x64 cell, plan view.
    double=False -> single horizontal bed (head at left).
    double=True  -> 2-story: two bunks stacked across the width axis."""
    base = pal
    if not double:
        w, h = 112, 48
        plan_frame(x0 + 8, y0 + 8, w, h, pal, cloth_key, head="left")
        return
    # two bunks stacked top / bottom, each with head at the left
    w, h = 112, 24
    plan_frame(x0 + 8, y0 + 4, w, h, pal, cloth_key, head="left")
    plan_frame(x0 + 8, y0 + 36, w, h, pal, cloth_key, head="left")
    # connecting posts (plan) at the right end
    draw.rectangle([x0 + 8 + w + 3, y0 + 4, x0 + 8 + w + 5, y0 + 60], fill=base["hi"])
    draw.rectangle([x0 + 10, y0 + 4, x0 + 12, y0 + 60], fill=base["hi"])


# --- Layout on the 8x8 grid ---
# Each entry: (kind, material, col, row[, double]).
#   single     -> 64x64   (1x1)
#   double     -> 64x128  (1x2, 2-story bunk)
#   horizontal -> 128x64  (2x1)
layout = [
    # Wood, single (1x1)
    ("single", "wood", 0, 0),
    # Iron, single (1x1)
    ("single", "iron", 1, 0),
    # Wood, double 2-story (1x2) — rows 0-1
    ("double", "wood", 2, 0),
    # Iron, double 2-story (1x2) — rows 0-1
    ("double", "iron", 3, 0),
    # Wood, horizontal single (2x1) — cols 4-5
    ("horizontal", "wood", 4, 0),
    # Iron, horizontal single (2x1) — cols 6-7
    ("horizontal", "iron", 6, 0),
    # Wood, horizontal double 2-story (2x1) — cols 4-5, row 2
    ("horizontal", "wood", 4, 2, True),
    # Iron, horizontal double 2-story (2x1) — cols 6-7, row 2
    ("horizontal", "iron", 6, 2, True),
    # Wood, single horizontal crib (2x1) — cols 0-1, row 2
    ("horizontal", "wood", 0, 2),
    # Iron, single horizontal crib (2x1) — cols 2-3, row 2
    ("horizontal", "iron", 2, 2),
]


def render_cell(cx, cy, kind, mat, double=False):
    """Render one cell. Some cells are 64x128 (double) or 128x64 (horizontal),
    drawn starting at the cell's top-left corner within the grid."""
    if mat == "wood":
        pal = W
    else:
        pal = M
    if kind == "single":
        draw_single(cx, cy, pal, mat)
    elif kind == "double":
        draw_double(cx, cy, pal, mat)
    elif kind == "horizontal":
        draw_horizontal(cx, cy, pal, mat, double=double)


# Draw each item of the layout.
for item in layout:
    kind, mat, col, row = item[0], item[1], item[2], item[3]
    double = item[4] if len(item) > 4 else False
    x0 = col * CELL
    y0 = row * CELL
    render_cell(x0, y0, kind, mat, double=double)

# Save output natively
img.save("bed_tiles.png")
print("Successfully generated bed_tiles.png (512x512) with beds/cribs and transparency.")
