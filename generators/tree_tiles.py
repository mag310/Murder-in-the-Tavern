from PIL import Image, ImageDraw
from random import Random, randint, uniform

# Spritesheet specifications
TILE_SIZE = 64
COLS = 4
WIDTH = TILE_SIZE * COLS  # 256 px
HEIGHT = TILE_SIZE        # 64 px

# Create transparency canvas
img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Palettes (Dark Fantasy Style) — all four are green leafy trees,
# each with a distinct trunk shape and a different shade of green.
tree_palettes = {
    0: {  # Old Oak — thick gnarled trunk, dense dark-green canopy
        "trunk":   (74, 53, 34),
        "trunk_hi":(110, 80, 50),
        "leaves":  [ (30, 52, 30), (46, 75, 43), (62, 92, 52) ],
        "style":   "thick",
    },
    1: {  # Bushy tree — short stout trunk, wide layered foliage
        "trunk":   (80, 60, 38),
        "trunk_hi":(115, 90, 55),
        "leaves":  [ (40, 70, 38), (60, 95, 48), (84, 120, 60) ],
        "style":   "short",
    },
    2: {  # Slender tree — thin straight trunk, tall narrow canopy
        "trunk":   (60, 44, 32),
        "trunk_hi":(90, 70, 48),
        "leaves":  [ (44, 66, 42), (64, 90, 52), (92, 118, 66) ],
        "style":   "thin",
    },
    3: {  # Fruit / berry tree — slim trunk, bright-green dotted canopy
        "trunk":   (66, 48, 36),
        "trunk_hi":(96, 72, 50),
        "leaves":  [ (55, 80, 40), (85, 115, 52), (110, 140, 65) ],
        "style":   "thin",
    },
}

def clip(v, lo, hi):
    return max(lo, min(hi, v))

def draw_tree(idx, x0, y0):
    x1, y1 = x0 + TILE_SIZE, y0 + TILE_SIZE
    pal = tree_palettes[idx]
    rnd = Random(1000 + idx)  # deterministic per tile
    cx = x0 + TILE_SIZE // 2   # center x
    base_y = y1 - 6            # ground line

    trunk = pal["trunk"]
    trunk_hi = pal["trunk_hi"]
    leaves = pal["leaves"]
    trunk_style = pal["style"]

    # --- Trunk (always within tile) ---
    if trunk_style == "thick":
        draw.rectangle([cx - 7, y0 + 24, cx + 7, base_y], fill=trunk)
        draw.rectangle([cx - 3, y0 + 24, cx - 1, base_y], fill=trunk_hi)
        draw.ellipse([cx - 9, base_y - 14, cx + 9, base_y], fill=trunk)  # root flare
        draw.line([cx - 4, y0 + 34, cx - 12, y0 + 24], fill=trunk, width=3)
        draw.line([cx + 3, y0 + 30, cx + 12, y0 + 22], fill=trunk, width=3)
        draw.line([cx, y0 + 26, cx, y0 + 14], fill=trunk, width=3)
    elif trunk_style == "short":
        draw.rectangle([cx - 6, y0 + 34, cx + 6, base_y], fill=trunk)
        draw.rectangle([cx - 3, y0 + 34, cx - 1, base_y], fill=trunk_hi)
        draw.ellipse([cx - 8, base_y - 10, cx + 8, base_y], fill=trunk)
    else:  # "thin" — straight slim trunk
        draw.rectangle([cx - 3, y0 + 26, cx + 3, base_y], fill=trunk)
        draw.rectangle([cx - 1, y0 + 26, cx + 1, base_y], fill=trunk_hi)
        draw.ellipse([cx - 5, base_y - 10, cx + 5, base_y], fill=trunk)

    # --- Canopy: green, clipped to tile bounds ---
    # every ellipse is clipped to (x0+2, y0+TOP_GAP, x1-2, y1-2) so no
    # foliage ever bleeds outside the 64x64 tile, and the crown stays
    # a few pixels below the top edge instead of touching it.
    TOP_GAP = 10
    top = y0 + TOP_GAP
    bot = y1 - 2
    left = x0 + 2
    right = x1 - 2

    if trunk_style == "short":
        # wide low crown sitting on top of the short trunk
        blobs = [
            (cx - 18, y0 + 24, 20),
            (cx + 18, y0 + 24, 20),
            (cx, y0 + 14, 24),
            (cx - 8, y0 + 18, 18),
            (cx + 8, y0 + 18, 18),
        ]
    elif trunk_style == "thin":
        # tall narrow crown
        blobs = [
            (cx, y0 + 10, 16),
            (cx - 10, y0 + 18, 14),
            (cx + 10, y0 + 18, 14),
            (cx, y0 + 24, 18),
            (cx - 6, y0 + 28, 12),
            (cx + 6, y0 + 28, 12),
        ]
    else:  # "thick" — full round crown
        blobs = [
            (cx - 14, y0 + 12, 22),
            (cx + 14, y0 + 14, 20),
            (cx, y0 + 8, 24),
            (cx - 20, y0 + 22, 16),
            (cx + 20, y0 + 22, 16),
            (cx, y0 + 22, 20),
        ]

    for j, (bx, by, r) in enumerate(blobs):
        shade = leaves[min(j, len(leaves) - 1)]
        for _ in range(7):
            ox = int(uniform(-r, r) * 0.5)
            oy = int(uniform(-r, r) * 0.5)
            rr = int(r * uniform(0.5, 0.9))
            ex0 = clip(bx - rr + ox, left, right)
            ey0 = clip(by - rr + oy, top, bot)
            ex1 = clip(bx + rr + ox, left, right)
            ey1 = clip(by + rr + oy, top, bot)
            if ex1 - ex0 >= 1 and ey1 - ey0 >= 1:
                draw.ellipse([ex0, ey0, ex1, ey1], fill=shade)
    # highlights (clipped)
    draw.ellipse([clip(cx - 8, left, right), clip(y0 + 4, top, bot),
                  clip(cx + 6, left, right), clip(y0 + 16, top, bot)],
                 fill=leaves[-1])
    # fruit dots on the berry tree, clipped
    if idx == 3:
        for _ in range(8):
            fx = clip(cx + randint(-14, 14), left, right)
            fy = clip(y0 + randint(6, 30), top, bot)
            draw.ellipse([fx, fy, fx + 3, fy + 3], fill=(150, 40, 40))


for i in range(COLS):
    x0 = i * TILE_SIZE
    draw_tree(i, x0, 0)

# Save output natively
img.save("tree_tiles.png")
print("Successfully generated tree_tiles.png (256x64) with 4 distinct trees and transparency.")
