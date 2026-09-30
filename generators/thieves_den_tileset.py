from PIL import Image, ImageDraw, ImageFilter
from random import Random

# --- Thieves' den tileset (dark fantasy, slums). ---
# 256x256 spritesheet, 4 cols x 4 rows of 64x64 tiles (id 0..15).
# Style: grimy, dark fantasy, city slums.
# Palette: dark grey, brown, swamp green, muted blue.
TILE = 64
COLS = 4
ROWS = 4
WIDTH = TILE * COLS   # 256 px
HEIGHT = TILE * ROWS  # 256 px

img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)


def shade(c, f):
    """Multiply an RGB(A) tuple by a factor (clip to 0..255)."""
    out = [max(0, min(255, int(v * f))) for v in c[:3]]
    if len(c) == 4:
        out.append(c[3])
    return tuple(out)


def noisy(d, x0, y0, w, h, base, jitter=10, seed=None):
    """Fill rect (x0,y0,w,h) with per-pixel jittered noise over `base`."""
    rnd = Random(seed)
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            f = 1.0 + rnd.uniform(-jitter / 100.0, jitter / 100.0)
            d.point((x, y), fill=shade(base, f))


# --- Palettes (dark fantasy) ---
GREY = (58, 58, 66)       # dark grey stone
GREY_HI = (96, 96, 104)
BROWN = (84, 58, 40)      # dark brown brick/wood
BROWN_HI = (128, 92, 64)
WOOD = (92, 64, 42)
WOOD_HI = (140, 100, 66)
SWAMP = (46, 62, 44)      # swamp green water
SWAMP_HI = (74, 96, 68)
MUD = (70, 56, 40)        # dirt / mud
MUD_HI = (96, 78, 56)
BLUE = (52, 66, 92)       # muted blue
BLUE_HI = (86, 108, 140)
RUST = (120, 96, 88)      # worn metal
RUST_HI = (176, 168, 160)
DARKRED = (86, 36, 36)    # dark red carpet
DARKRED_HI = (140, 64, 60)
BLACK = (22, 22, 26)


def cell(col, row):
    return (col * TILE, row * TILE)


# 0 — stone cobblestone (dark grey, cracks)
def tile_cobble(x0, y0, rnd):
    noisy(draw, x0, y0, TILE, TILE, GREY, jitter=12, seed=0)
    # cobble stones: rows of rounded stones
    for row in range(4):
        y = y0 + row * 16
        off = 8 if row % 2 else 0
        for i in range(5):
            sx = x0 + i * 16 + off
            draw.ellipse([sx - 8, y - 7, sx + 8, y + 9], fill=shade(GREY, 1.08))
            draw.ellipse([sx - 8, y - 7, sx + 8, y + 9], outline=BLACK, width=1)
    # cracks
    for _ in range(7):
        cx = x0 + rnd.randint(0, TILE - 1)
        cy = y0 + rnd.randint(0, TILE - 1)
        draw.line([cx, cy, cx + rnd.randint(-6, 6), cy + rnd.randint(-6, 6)],
                   fill=BLACK, width=1)


# 1 — brick wall (dark brown, uneven bricks)
def tile_brick(x0, y0, rnd):
    noisy(draw, x0, y0, TILE, TILE, BROWN, jitter=10, seed=1)
    bw, bh = 30, 13
    for row in range(5):
        y = y0 + row * 14
        off = 15 if row % 2 else 0
        for i in range(-1, 3):
            bx = x0 + i * bw + off
            draw.rectangle([bx, y, bx + bw, y + bh], fill=shade(BROWN, 1.05))
            draw.rectangle([bx, y, bx + bw, y + bh], outline=BLACK, width=1)
            # mortar highlight
            draw.line([bx, y + 1, bx + bw, y + 1], fill=shade(BROWN_HI, 0.8), width=1)


# 2 — wooden crate (worn, metal corners)
def tile_crate(x0, y0, rnd):
    noisy(draw, x0 + 10, y0 + 8, TILE - 20, TILE - 16, WOOD, jitter=10, seed=2)
    draw.rectangle([x0 + 8, y0 + 6, x0 + 56, y0 + 58], fill=shade(WOOD, 0.8))
    draw.rectangle([x0 + 10, y0 + 8, x0 + 54, y0 + 56], fill=WOOD)
    # plank lines
    for i in range(1, 5):
        y = y0 + 8 + i * 10
        draw.line([x0 + 10, y, x0 + 54, y], fill=BLACK, width=1)
    # metal corners
    for (cx, cy) in [(x0 + 8, y0 + 6), (x0 + 46, y0 + 6),
                     (x0 + 8, y0 + 46), (x0 + 46, y0 + 46)]:
        draw.rectangle([cx, cy, cx + 10, cy + 10], fill=RUST)
        draw.rectangle([cx, cy, cx + 10, cy + 10], outline=RUST_HI, width=1)
        draw.ellipse([cx + 3, cy + 3, cx + 7, cy + 7], fill=BLACK)
    # shadow
    draw.rectangle([x0 + 12, y0 + 58, x0 + 58, y0 + 60], fill=(0, 0, 0, 60))


# 3 — barrel (wood, hoops)
def tile_barrel(x0, y0, rnd):
    noisy(draw, x0 + 16, y0 + 6, TILE - 32, TILE - 12, WOOD, jitter=10, seed=3)
    cx = x0 + TILE // 2
    # barrel body (vertical staves)
    draw.ellipse([x0 + 16, y0 + 6, x0 + 48, y0 + 58], fill=WOOD)
    for i in range(6):
        sx = x0 + 18 + i * 5
        draw.line([sx, y0 + 8, sx, y0 + 56], fill=shade(WOOD, 0.85), width=2)
    # hoops
    for y in (y0 + 12, y0 + 32, y0 + 52):
        draw.line([x0 + 16, y, x0 + 48, y], fill=RUST, width=3)
        draw.line([x0 + 16, y + 1, x0 + 48, y + 1], fill=shade(RUST_HI, 0.7), width=1)
    # top rim
    draw.ellipse([x0 + 16, y0 + 4, x0 + 48, y0 + 14], fill=shade(WOOD, 1.1))
    draw.ellipse([x0 + 18, y0 + 6, x0 + 46, y0 + 12], fill=shade(WOOD, 0.6))
    # shadow
    draw.ellipse([x0 + 18, y0 + 58, x0 + 50, y0 + 62], fill=(0, 0, 0, 70))


# 4 — market stall (wood, awning)
def tile_stall(x0, y0, rnd):
    noisy(draw, x0 + 6, y0 + 26, TILE - 12, TILE - 30, WOOD, jitter=8, seed=4)
    # stall counter
    draw.rectangle([x0 + 6, y0 + 30, x0 + 58, y0 + 58], fill=WOOD)
    draw.rectangle([x0 + 6, y0 + 30, x0 + 58, y0 + 34], fill=shade(WOOD, 1.2))
    draw.line([x0 + 6, y0 + 46, x0 + 58, y0 + 46], fill=BLACK, width=1)
    # posts
    draw.rectangle([x0 + 6, y0 + 12, x0 + 10, y0 + 58], fill=shade(WOOD, 0.8))
    draw.rectangle([x0 + 54, y0 + 12, x0 + 58, y0 + 58], fill=shade(WOOD, 0.8))
    # awning (striped)
    draw.polygon([(x0 + 4, y0 + 12), (x0 + 60, y0 + 12),
                  (x0 + 56, y0 + 28), (x0 + 8, y0 + 28)], fill=BLUE)
    for i in range(6):
        ax = x0 + 6 + i * 9
        draw.line([ax, y0 + 12, ax + 4, y0 + 28], fill=shade(BLUE, 1.4), width=2)
    # goods on counter
    for i in range(4):
        gx = x0 + 12 + i * 11
        draw.ellipse([gx, y0 + 22, gx + 8, y0 + 30], fill=shade(BROWN_HI, 0.9))


# 5 — dirty water (dark green, highlights)
def tile_water(x0, y0, rnd):
    noisy(draw, x0, y0, TILE, TILE, SWAMP, jitter=14, seed=5)
    # ripples / highlights
    for _ in range(18):
        rx = x0 + rnd.randint(0, TILE - 8)
        ry = y0 + rnd.randint(0, TILE - 8)
        rw = rnd.randint(3, 10)
        draw.line([rx, ry, rx + rw, ry], fill=shade(SWAMP_HI, 0.9), width=1)
    # darker muck patches
    for _ in range(10):
        px = x0 + rnd.randint(2, TILE - 8)
        py = y0 + rnd.randint(2, TILE - 8)
        draw.ellipse([px, py, px + rnd.randint(4, 10), py + rnd.randint(4, 10)],
                     fill=shade(SWAMP, 0.6))
    # a few bright specular glints
    for _ in range(6):
        gx = x0 + rnd.randint(2, TILE - 4)
        gy = y0 + rnd.randint(2, TILE - 4)
        draw.point((gx, gy), fill=shade(SWAMP_HI, 1.6))


# 6 — dirt / mud
def tile_dirt(x0, y0, rnd):
    noisy(draw, x0, y0, TILE, TILE, MUD, jitter=12, seed=6)
    # pebbles / debris
    for _ in range(26):
        px = x0 + rnd.randint(0, TILE - 4)
        py = y0 + rnd.randint(0, TILE - 4)
        draw.ellipse([px, py, px + rnd.randint(2, 6), py + rnd.randint(2, 6)],
                     fill=shade(MUD, rnd.choice((0.7, 1.2))))
    # a few dark stains
    for _ in range(8):
        sx = x0 + rnd.randint(0, TILE - 12)
        sy = y0 + rnd.randint(0, TILE - 12)
        draw.ellipse([sx, sy, sx + rnd.randint(6, 14), sy + rnd.randint(6, 14)],
                     fill=shade(MUD, 0.55))


# 7 — rope / cable
def tile_rope(x0, y0, rnd):
    noisy(draw, x0, y0, TILE, TILE, MUD, jitter=8, seed=7)  # faint ground
    rope = (150, 120, 70)
    # coiled rope
    for r in range(8, 30, 4):
        draw.ellipse([x0 + 12, y0 + 12, x0 + 52, y0 + 52],
                     outline=rope, width=3)
        draw.ellipse([x0 + 12, y0 + 12, x0 + 52, y0 + 52],
                     outline=shade(rope, 0.6), width=1)
    # loose strand
    draw.arc([x0 + 30, y0 + 20, x0 + 58, y0 + 48], 0, 180, fill=rope, width=3)
    # twist highlights
    for _ in range(30):
        px = x0 + rnd.randint(14, 50)
        py = y0 + rnd.randint(14, 50)
        if 18 <= (px - (x0 + 32)) ** 2 + (py - (y0 + 32)) ** 2 <= 900:
            draw.point((px, py), fill=shade(rope, 1.4))


# 8 — lantern (dim light)
def tile_lantern(x0, y0, rnd):
    noisy(draw, x0, y0, TILE, TILE, MUD, jitter=6, seed=8)
    cx = x0 + TILE // 2
    # pole
    draw.rectangle([cx - 2, y0 + 4, cx + 2, y0 + 44], fill=shade(WOOD, 0.9))
    # bracket
    draw.line([cx, y0 + 12, cx + 16, y0 + 16], fill=shade(WOOD, 0.8), width=2)
    # housing
    draw.rectangle([cx + 8, y0 + 16, cx + 26, y0 + 34], outline=RUST, width=2)
    # dim glow
    glow = img.crop((0, 0, WIDTH, HEIGHT))
    light = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ld = ImageDraw.Draw(light)
    for r, a in [(40, 30), (28, 50), (16, 80)]:
        ld.ellipse([cx + 17 - r, y0 + 25 - r, cx + 17 + r, y0 + 25 + r],
                   fill=(220, 180, 90, a))
    light = light.filter(ImageFilter.GaussianBlur(6))
    img.alpha_composite(light)
    # flame core
    draw.ellipse([cx + 13, y0 + 20, cx + 21, y0 + 30], fill=(250, 220, 130))
    # ground light pool
    draw.ellipse([cx - 6, y0 + 44, cx + 40, y0 + 60], fill=(200, 170, 90, 40))
    draw.ellipse([cx - 2, y0 + 48, cx + 30, y0 + 58], fill=(220, 190, 110, 60))


# 9 — shadow (semi-transparent)
def tile_shadow(x0, y0, rnd):
    light = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    sd = ImageDraw.Draw(light)
    sd.ellipse([x0 + 6, y0 + 14, x0 + 58, y0 + 56], fill=(0, 0, 0, 130))
    sd.ellipse([x0 + 16, y0 + 24, x0 + 48, y0 + 50], fill=(0, 0, 0, 170))
    light = light.filter(ImageFilter.GaussianBlur(4))
    img.alpha_composite(light)


# 10 — rubble / trash
def tile_rubble(x0, y0, rnd):
    noisy(draw, x0, y0, TILE, TILE, MUD, jitter=10, seed=10)
    # scattered debris (broken planks, stones, cloth)
    for _ in range(12):
        px = x0 + rnd.randint(2, TILE - 14)
        py = y0 + rnd.randint(2, TILE - 14)
        c = rnd.choice([GREY, BROWN, RUST, DARKRED])
        draw.rectangle([px, py, px + rnd.randint(6, 14), py + rnd.randint(4, 10)],
                       fill=shade(c, rnd.uniform(0.7, 1.1)))
    # a few stone chunks
    for _ in range(8):
        px = x0 + rnd.randint(2, TILE - 8)
        py = y0 + rnd.randint(2, TILE - 8)
        draw.ellipse([px, py, px + rnd.randint(4, 8), py + rnd.randint(4, 8)],
                     fill=shade(GREY, rnd.uniform(0.8, 1.1)))
    # tattered cloth scrap
    draw.polygon([(x0 + 8, y0 + 40), (x0 + 24, y0 + 38), (x0 + 20, y0 + 50),
                  (x0 + 30, y0 + 52), (x0 + 12, y0 + 56)], fill=shade(DARKRED, 0.8))


# 11 — carpet (dark red, tattered)
def tile_carpet(x0, y0, rnd):
    noisy(draw, x0 + 4, y0 + 4, TILE - 8, TILE - 8, DARKRED, jitter=8, seed=11)
    draw.rectangle([x0 + 4, y0 + 4, x0 + 60, y0 + 60], fill=DARKRED)
    # border
    draw.rectangle([x0 + 4, y0 + 4, x0 + 60, y0 + 60], outline=shade(DARKRED_HI, 0.9), width=2)
    # diamond pattern
    for r in range(2):
        for c in range(2):
            dx = x0 + 18 + c * 24
            dy = y0 + 18 + r * 24
            draw.polygon([(dx, dy), (dx + 10, dy + 10), (dx, dy + 20),
                          (dx - 10, dy + 10)], outline=shade(DARKRED_HI, 0.8), width=1)
    # frayed / tattered edge (right side)
    for i in range(6):
        ty = y0 + 8 + i * 9
        draw.line([x0 + 58, ty, x0 + 64, ty + rnd.randint(-4, 4)],
                  fill=shade(DARKRED, 0.9), width=1)
    # a worn hole
    draw.ellipse([x0 + 30, y0 + 38, x0 + 42, y0 + 48], fill=shade(DARKRED, 0.4))


# 12 — table
def tile_table(x0, y0, rnd):
    noisy(draw, x0 + 12, y0 + 12, TILE - 24, TILE - 20, WOOD, jitter=8, seed=12)
    # top-down table (square top + legs hint)
    draw.ellipse([x0 + 18, y0 + 50, x0 + 46, y0 + 58], fill=(0, 0, 0, 60))  # shadow
    draw.rectangle([x0 + 12, y0 + 12, x0 + 52, y0 + 50], fill=WOOD)
    draw.rectangle([x0 + 12, y0 + 12, x0 + 52, y0 + 16], fill=shade(WOOD, 1.2))
    draw.rectangle([x0 + 12, y0 + 12, x0 + 16, y0 + 50], fill=shade(WOOD, 1.05))
    draw.rectangle([x0 + 12, y0 + 12, x0 + 52, y0 + 50], outline=BLACK, width=1)
    # plank grain
    for i in range(2, 5):
        y = y0 + 12 + i * 9
        draw.line([x0 + 14, y, x0 + 50, y], fill=shade(WOOD, 0.85), width=1)
    # legs
    for (lx, ly) in [(x0 + 14, y0 + 14), (x0 + 46, y0 + 14),
                     (x0 + 14, y0 + 44), (x0 + 46, y0 + 44)]:
        draw.ellipse([lx, ly, lx + 6, ly + 6], fill=shade(WOOD, 0.7))


# 13 — chair
def tile_chair(x0, y0, rnd):
    noisy(draw, x0 + 18, y0 + 14, TILE - 36, TILE - 22, WOOD, jitter=8, seed=13)
    draw.ellipse([x0 + 18, y0 + 50, x0 + 46, y0 + 58], fill=(0, 0, 0, 60))  # shadow
    # seat
    draw.rectangle([x0 + 18, y0 + 30, x0 + 46, y0 + 48], fill=WOOD)
    draw.rectangle([x0 + 18, y0 + 30, x0 + 46, y0 + 33], fill=shade(WOOD, 1.2))
    draw.rectangle([x0 + 18, y0 + 30, x0 + 46, y0 + 48], outline=BLACK, width=1)
    # backrest
    draw.rectangle([x0 + 18, y0 + 14, x0 + 46, y0 + 20], fill=shade(WOOD, 1.05))
    draw.rectangle([x0 + 20, y0 + 14, x0 + 22, y0 + 30], fill=shade(WOOD, 0.9))
    draw.rectangle([x0 + 42, y0 + 14, x0 + 44, y0 + 30], fill=shade(WOOD, 0.9))
    # legs
    for (lx, ly) in [(x0 + 18, y0 + 48), (x0 + 42, y0 + 48)]:
        draw.line([lx + 2, ly, lx + 2, ly + 8], fill=shade(WOOD, 0.8), width=2)


# 14 — crate 2 (open)
def tile_crate2(x0, y0, rnd):
    noisy(draw, x0 + 10, y0 + 18, TILE - 20, TILE - 26, WOOD, jitter=10, seed=14)
    # open box (lower box + open flaps up)
    draw.rectangle([x0 + 10, y0 + 30, x0 + 54, y0 + 56], fill=shade(WOOD, 0.7))
    draw.rectangle([x0 + 10, y0 + 30, x0 + 54, y0 + 56], outline=BLACK, width=1)
    # inner empty box
    draw.rectangle([x0 + 16, y0 + 36, x0 + 48, y0 + 52], fill=shade(WOOD, 0.45))
    # open flaps (tilted outward)
    draw.polygon([(x0 + 10, y0 + 30), (x0 + 16, y0 + 14), (x0 + 32, y0 + 16),
                  (x0 + 26, y0 + 30)], fill=shade(WOOD, 1.05))
    draw.polygon([(x0 + 28, y0 + 30), (x0 + 34, y0 + 16), (x0 + 50, y0 + 14),
                  (x0 + 54, y0 + 30)], fill=shade(WOOD, 0.95))
    # metal corners
    for (cx, cy) in [(x0 + 10, y0 + 30), (x0 + 44, y0 + 30)]:
        draw.rectangle([cx, cy, cx + 8, cy + 8], fill=RUST)
    # a couple of items spilling
    for _ in range(3):
        px = x0 + 16 + rnd.randint(0, 28)
        py = y0 + 38 + rnd.randint(0, 10)
        draw.ellipse([px, py, px + 6, py + 6], fill=shade(BROWN_HI, 0.9))
    draw.rectangle([x0 + 12, y0 + 56, x0 + 56, y0 + 58], fill=(0, 0, 0, 60))


# 15 — barrel 2 (broken)
def tile_barrel2(x0, y0, rnd):
    noisy(draw, x0 + 16, y0 + 8, TILE - 32, TILE - 16, WOOD, jitter=10, seed=15)
    cx = x0 + TILE // 2
    # cracked barrel
    draw.ellipse([x0 + 16, y0 + 8, x0 + 48, y0 + 58], fill=shade(WOOD, 0.8))
    for i in range(6):
        sx = x0 + 18 + i * 5
        draw.line([sx, y0 + 10, sx, y0 + 56], fill=shade(WOOD, 0.8), width=2)
    # a single broken hoop
    draw.line([x0 + 16, y0 + 30, x0 + 48, y0 + 30], fill=shade(RUST, 0.7), width=2)
    # big crack (zig-zag)
    pts = [(cx, y0 + 10)]
    yy = y0 + 10
    for _ in range(8):
        yy += 5
        pts.append((cx + rnd.randint(-6, 6), yy))
    draw.line(pts, fill=BLACK, width=2)
    # spilled liquid
    for _ in range(14):
        px = x0 + rnd.randint(10, 50)
        py = y0 + rnd.randint(50, 58)
        draw.ellipse([px, py, px + rnd.randint(3, 7), py + rnd.randint(2, 4)],
                     fill=shade(SWAMP, 0.7))
    # missing stave (gap)
    draw.line([x0 + 38, y0 + 12, x0 + 40, y0 + 54], fill=shade(WOOD, 0.4), width=3)
    draw.ellipse([x0 + 18, y0 + 58, x0 + 50, y0 + 62], fill=(0, 0, 0, 70))


TILES = [
    tile_cobble, tile_brick, tile_crate, tile_barrel,
    tile_stall, tile_water, tile_dirt, tile_rope,
    tile_lantern, tile_shadow, tile_rubble, tile_carpet,
    tile_table, tile_chair, tile_crate2, tile_barrel2,
]


def main():
    rnd = Random(2026)
    for idx, fn in enumerate(TILES):
        col = idx % COLS
        row = idx // COLS
        x0, y0 = cell(col, row)
        fn(x0, y0, rnd)
    img.save("thieves_den_tileset.png")
    print("Successfully generated thieves_den_tileset.png (%dx%d): 16 tiles (4x4)."
          % (WIDTH, HEIGHT))
    write_tsx()


# Per-tile properties: collision for solid objects, water for the pool.
PROPERTIES = {
    1: {"type": "wall", "collision": "true"},
    2: {"type": "crate", "collision": "true"},
    3: {"type": "barrel", "collision": "true"},
    4: {"type": "stall", "collision": "true"},
    5: {"type": "water", "collision": "false"},
    6: {"type": "dirt"},
    7: {"type": "rope"},
    8: {"type": "lantern"},
    9: {"type": "shadow"},
    10: {"type": "rubble"},
    11: {"type": "carpet"},
    12: {"type": "table"},
    13: {"type": "chair"},
    14: {"type": "crate2", "collision": "true"},
    15: {"type": "barrel2", "collision": "true"},
}


def write_tsx():
    """Emit a Tiled .tsx tileset definition matching thieves_den_tileset.png."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<tileset version="1.10" name="thieves_den_tileset" '
        'tilewidth="64" tileheight="64" '
        'tilecount="%d" columns="%d" rows="%d">' % (COLS * ROWS, COLS, ROWS),
        '  <image source="thieves_den_tileset.png" width="256" height="256"/>',
    ]
    for idx, props in PROPERTIES.items():
        lines.append('  <tile id="%d">' % idx)
        for key, val in props.items():
            lines.append('    <property name="%s" value="%s"/>' % (key, val))
        lines.append('  </tile>')
    lines.append('</tileset>')
    text = "\n".join(lines) + "\n"
    with open("thieves_den_tileset.tsx", "w") as fh:
        fh.write(text)
    print("Successfully generated thieves_den_tileset.tsx: %d tiles with properties."
          % len(PROPERTIES))


main()
