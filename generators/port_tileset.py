import os
from PIL import Image, ImageDraw, ImageFilter
from random import Random

# --- Harbour / port tileset (dark fantasy seaport). ---
# 256x256 spritesheet, 4 cols x 4 rows of 64x64 tiles (id 0..15).
# Style: seaport, salt, tar, wood, water.
# Palette: grey-brown, dark blue, green, rust.
TILE = 64
COLS = 4
ROWS = 4
WIDTH = TILE * COLS   # 256 px
HEIGHT = TILE * ROWS  # 256 px

img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Output lives next to the maps (../maps/ from the generators/ dir).
OUT_PNG = os.path.join(os.path.dirname(__file__), "..", "maps", "port_tileset.png")
OUT_TSX = os.path.join(os.path.dirname(__file__), "..", "maps", "port_tileset.tsx")


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


# --- Palettes (seaport) ---
WOOD = (108, 84, 60)       # grey-brown deck planks
WOOD_HI = (150, 122, 92)
WOOD_DK = (64, 50, 38)
STONE = (70, 74, 82)       # dark stone / brick
STONE_HI = (108, 112, 122)
STONE_DK = (40, 44, 52)
RUST = (132, 92, 70)       # rust
RUST_HI = (186, 146, 120)
BLUE = (38, 58, 92)       # dark blue water
BLUE_HI = (66, 96, 132)
GREEN = (48, 70, 62)       # green (algae / net)
GREEN_HI = (80, 110, 96)
SALT = (150, 150, 138)     # salt / light dust
BLACK = (22, 22, 26)
DARKRED = (86, 44, 44)


def cell(col, row):
    return (col * TILE, row * TILE)


# 0 — dock planks (grey-brown, gaps)
def tile_planks(x0, y0, rnd):
    noisy(draw, x0, y0, TILE, TILE, WOOD, jitter=10, seed=0)
    # vertical planks with dark seams between them
    for i in range(6):
        px = x0 + i * 11
        draw.rectangle([px, y0, px + 9, y0 + TILE], fill=shade(WOOD, 0.95))
        draw.line([px + 9, y0, px + 9, y0 + TILE], fill=BLACK, width=1)
        # grain highlights
        for g in range(3):
            gy = y0 + rnd.randint(4, TILE - 14)
            draw.line([px + 2, gy, px + 7, gy + rnd.randint(2, 8)],
                      fill=shade(WOOD_HI, 0.7), width=1)
    # a couple of nails
    for _ in range(8):
        nx = x0 + rnd.randint(2, TILE - 3)
        ny = y0 + rnd.randint(2, TILE - 3)
        draw.ellipse([nx, ny, nx + 2, ny + 2], fill=RUST_HI)


# 1 — warehouse wall (dark stone / brick)
def tile_wall(x0, y0, rnd):
    noisy(draw, x0, y0, TILE, TILE, STONE, jitter=12, seed=1)
    bw, bh = 30, 13
    for row in range(5):
        y = y0 + row * 14
        off = 15 if row % 2 else 0
        for i in range(-1, 3):
            bx = x0 + i * bw + off
            draw.rectangle([bx, y, bx + bw, y + bh], fill=shade(STONE, 1.05))
            draw.rectangle([bx, y, bx + bw, y + bh], outline=STONE_DK, width=1)
            draw.line([bx, y + 1, bx + bw, y + 1], fill=shade(STONE_HI, 0.7), width=1)
    # tar stains
    for _ in range(6):
        sx = x0 + rnd.randint(0, TILE - 14)
        sy = y0 + rnd.randint(0, TILE - 14)
        draw.ellipse([sx, sy, sx + rnd.randint(6, 14), sy + rnd.randint(6, 14)],
                     fill=shade(STONE, 0.5))


# 2 — sea crate (with marking)
def tile_crate(x0, y0, rnd):
    noisy(draw, x0 + 8, y0 + 8, TILE - 16, TILE - 16, WOOD, jitter=10, seed=2)
    draw.rectangle([x0 + 8, y0 + 8, x0 + 56, y0 + 56], fill=shade(WOOD, 0.75))
    draw.rectangle([x0 + 10, y0 + 10, x0 + 54, y0 + 54], fill=WOOD)
    for i in range(1, 5):
        y = y0 + 10 + i * 9
        draw.line([x0 + 10, y, x0 + 54, y], fill=BLACK, width=1)
    # metal corners
    for (cx, cy) in [(x0 + 8, y0 + 8), (x0 + 46, y0 + 8),
                     (x0 + 8, y0 + 46), (x0 + 46, y0 + 46)]:
        draw.rectangle([cx, cy, cx + 10, cy + 10], fill=RUST)
        draw.rectangle([cx, cy, cx + 10, cy + 10], outline=RUST_HI, width=1)
    # marking (chalked letters / symbol)
    draw.rectangle([x0 + 22, y0 + 22, x0 + 42, y0 + 42], outline=SALT, width=2)
    draw.line([x0 + 22, y0 + 22, x0 + 42, y0 + 42], fill=SALT, width=2)
    draw.line([x0 + 42, y0 + 22, x0 + 22, y0 + 42], fill=SALT, width=2)
    draw.ellipse([x0 + 12, y0 + 56, x0 + 56, y0 + 58], fill=(0, 0, 0, 60))


# 3 — barrel (with salted fish)
def tile_barrel(x0, y0, rnd):
    noisy(draw, x0 + 16, y0 + 8, TILE - 32, TILE - 16, WOOD, jitter=10, seed=3)
    draw.ellipse([x0 + 16, y0 + 8, x0 + 48, y0 + 58], fill=WOOD)
    for i in range(6):
        sx = x0 + 18 + i * 5
        draw.line([sx, y0 + 10, sx, y0 + 56], fill=shade(WOOD, 0.85), width=2)
    # hoops
    for y in (y0 + 14, y0 + 32, y0 + 50):
        draw.line([x0 + 16, y, x0 + 48, y], fill=RUST, width=3)
        draw.line([x0 + 16, y + 1, x0 + 48, y + 1], fill=shade(RUST_HI, 0.7), width=1)
    # rim
    draw.ellipse([x0 + 16, y0 + 6, x0 + 48, y0 + 16], fill=shade(WOOD, 1.1))
    draw.ellipse([x0 + 18, y0 + 8, x0 + 46, y0 + 14], fill=shade(WOOD, 0.6))
    # salted fish poking out the top (pale)
    for i in range(3):
        fx = x0 + 22 + i * 8
        draw.ellipse([fx, y0 + 8, fx + 9, y0 + 14], fill=shade(SALT, 0.9))
        draw.line([fx + 1, y0 + 10, fx + 8, y0 + 12], fill=shade(BLUE, 0.7), width=1)
    draw.ellipse([x0 + 18, y0 + 58, x0 + 50, y0 + 62], fill=(0, 0, 0, 70))


# 4 — stall / table
def tile_stall(x0, y0, rnd):
    noisy(draw, x0 + 6, y0 + 26, TILE - 12, TILE - 26, WOOD, jitter=8, seed=4)
    # counter
    draw.rectangle([x0 + 6, y0 + 30, x0 + 58, y0 + 58], fill=WOOD)
    draw.rectangle([x0 + 6, y0 + 30, x0 + 58, y0 + 34], fill=shade(WOOD, 1.2))
    draw.line([x0 + 6, y0 + 46, x0 + 58, y0 + 46], fill=BLACK, width=1)
    # posts
    draw.rectangle([x0 + 6, y0 + 12, x0 + 10, y0 + 58], fill=shade(WOOD, 0.8))
    draw.rectangle([x0 + 54, y0 + 12, x0 + 58, y0 + 58], fill=shade(WOOD, 0.8))
    # striped awning
    draw.polygon([(x0 + 4, y0 + 12), (x0 + 60, y0 + 12),
                  (x0 + 56, y0 + 28), (x0 + 8, y0 + 28)], fill=BLUE)
    for i in range(6):
        ax = x0 + 6 + i * 9
        draw.line([ax, y0 + 12, ax + 4, y0 + 28], fill=shade(BLUE, 1.4), width=2)
    # goods (fish / crates)
    for i in range(4):
        gx = x0 + 12 + i * 11
        draw.ellipse([gx, y0 + 22, gx + 8, y0 + 30], fill=shade(SALT, 0.85))


# 5 — water (dark blue, waves)
def tile_water(x0, y0, rnd):
    noisy(draw, x0, y0, TILE, TILE, BLUE, jitter=14, seed=5)
    # wave strokes
    for _ in range(20):
        rx = x0 + rnd.randint(0, TILE - 8)
        ry = y0 + rnd.randint(0, TILE - 8)
        rw = rnd.randint(3, 11)
        draw.line([rx, ry, rx + rw, ry], fill=shade(BLUE_HI, 0.9), width=1)
    # foam crests
    for _ in range(8):
        fx = x0 + rnd.randint(2, TILE - 6)
        fy = y0 + rnd.randint(2, TILE - 6)
        draw.line([fx, fy, fx + 5, fy - 2], fill=shade(SALT, 0.7), width=1)
    # green algae patches
    for _ in range(9):
        px = x0 + rnd.randint(2, TILE - 10)
        py = y0 + rnd.randint(2, TILE - 10)
        draw.ellipse([px, py, px + rnd.randint(4, 10), py + rnd.randint(4, 10)],
                     fill=shade(GREEN, 0.7))
    # specular glints
    for _ in range(6):
        gx = x0 + rnd.randint(2, TILE - 4)
        gy = y0 + rnd.randint(2, TILE - 4)
        draw.point((gx, gy), fill=shade(BLUE_HI, 1.7))


# 6 — wet sand / mud
def tile_sand(x0, y0, rnd):
    noisy(draw, x0, y0, TILE, TILE, (96, 92, 78), jitter=12, seed=6)
    # pebbles / shell bits
    for _ in range(28):
        px = x0 + rnd.randint(0, TILE - 4)
        py = y0 + rnd.randint(0, TILE - 4)
        draw.ellipse([px, py, px + rnd.randint(2, 6), py + rnd.randint(2, 6)],
                     fill=shade((96, 92, 78), rnd.choice((0.7, 1.2))))
    # wet dark stains
    for _ in range(8):
        sx = x0 + rnd.randint(0, TILE - 14)
        sy = y0 + rnd.randint(0, TILE - 14)
        draw.ellipse([sx, sy, sx + rnd.randint(6, 14), sy + rnd.randint(6, 14)],
                     fill=shade((96, 92, 78), 0.5))
    # a shell
    sx, sy = x0 + 26, y0 + 30
    draw.ellipse([sx, sy, sx + 10, sy + 8], fill=shade(SALT, 0.8))
    draw.line([sx + 5, sy, sx + 5, sy + 8], fill=shade(SALT, 0.5), width=1)


# 7 — rope
def tile_rope(x0, y0, rnd):
    noisy(draw, x0, y0, TILE, TILE, (96, 92, 78), jitter=8, seed=7)
    rope = (150, 124, 74)
    # coiled rope
    for r in range(8, 30, 4):
        draw.ellipse([x0 + 12, y0 + 12, x0 + 52, y0 + 52],
                     outline=rope, width=3)
        draw.ellipse([x0 + 12, y0 + 12, x0 + 52, y0 + 52],
                     outline=shade(rope, 0.6), width=1)
    # loose strand
    draw.arc([x0 + 30, y0 + 18, x0 + 58, y0 + 48], 0, 180, fill=rope, width=3)
    # twist highlights
    for _ in range(30):
        px = x0 + rnd.randint(14, 50)
        py = y0 + rnd.randint(14, 50)
        if 16 <= (px - (x0 + 32)) ** 2 + (py - (y0 + 32)) ** 2 <= 900:
            draw.point((px, py), fill=shade(rope, 1.4))


# 8 — lantern (dim light)
def tile_lantern(x0, y0, rnd):
    noisy(draw, x0, y0, TILE, TILE, (96, 92, 78), jitter=6, seed=8)
    cx = x0 + TILE // 2
    # pole
    draw.rectangle([cx - 2, y0 + 4, cx + 2, y0 + 44], fill=shade(WOOD, 0.9))
    # bracket
    draw.line([cx, y0 + 12, cx + 16, y0 + 16], fill=shade(WOOD, 0.8), width=2)
    # housing
    draw.rectangle([cx + 8, y0 + 16, cx + 26, y0 + 34], outline=RUST, width=2)
    # dim glow
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


# 10 — rubble / debris
def tile_rubble(x0, y0, rnd):
    noisy(draw, x0, y0, TILE, TILE, (96, 92, 78), jitter=10, seed=10)
    # scattered debris (planks, stones, tar chunks)
    for _ in range(12):
        px = x0 + rnd.randint(2, TILE - 14)
        py = y0 + rnd.randint(2, TILE - 14)
        c = rnd.choice([STONE, WOOD, RUST, DARKRED])
        draw.rectangle([px, py, px + rnd.randint(6, 14), py + rnd.randint(4, 10)],
                       fill=shade(c, rnd.uniform(0.7, 1.1)))
    # stone chunks
    for _ in range(8):
        px = x0 + rnd.randint(2, TILE - 8)
        py = y0 + rnd.randint(2, TILE - 8)
        draw.ellipse([px, py, px + rnd.randint(4, 8), py + rnd.randint(4, 8)],
                     fill=shade(STONE, rnd.uniform(0.8, 1.1)))
    # tar stain
    draw.ellipse([x0 + 18, y0 + 36, x0 + 44, y0 + 52], fill=shade(BLACK, 1.4))


# 11 — net
def tile_net(x0, y0, rnd):
    noisy(draw, x0, y0, TILE, TILE, (96, 92, 78), jitter=6, seed=11)
    net = shade(GREEN_HI, 0.9)
    # net mesh (cross-hatch)
    step = 8
    for x in range(x0, x0 + TILE, step):
        draw.line([x, y0, x + 6, y0 + TILE], fill=net, width=1)
    for y in range(y0, y0 + TILE, step):
        draw.line([x0, y, x0 + TILE, y + 6], fill=net, width=1)
    # knots at intersections
    for x in range(x0, x0 + TILE, step):
        for y in range(y0, y0 + TILE, step):
            draw.ellipse([x, y, x + 2, y + 2], fill=shade(GREEN, 1.1))
    # a hanging loop / knot cluster
    draw.arc([x0 + 22, y0 + 18, x0 + 42, y0 + 38], 0, 180, fill=net, width=2)
    draw.ellipse([x0 + 30, y0 + 38, x0 + 34, y0 + 42], fill=shade(GREEN, 1.1))


# 12 — table 2
def tile_table(x0, y0, rnd):
    noisy(draw, x0 + 12, y0 + 12, TILE - 24, TILE - 20, WOOD, jitter=8, seed=12)
    draw.ellipse([x0 + 18, y0 + 50, x0 + 46, y0 + 58], fill=(0, 0, 0, 60))
    # round table (top-down)
    draw.ellipse([x0 + 14, y0 + 12, x0 + 50, y0 + 50], fill=WOOD)
    draw.ellipse([x0 + 14, y0 + 12, x0 + 50, y0 + 50], outline=BLACK, width=1)
    # sheen
    draw.ellipse([x0 + 18, y0 + 15, x0 + 30, y0 + 24], fill=shade(WOOD, 1.2))
    # plank ring
    draw.ellipse([x0 + 18, y0 + 16, x0 + 46, y0 + 46], outline=shade(WOOD, 0.85), width=1)
    # center hub
    draw.ellipse([x0 + 28, y0 + 26, x0 + 36, y0 + 34], fill=shade(WOOD, 0.7))
    # legs
    for (lx, ly) in [(x0 + 18, y0 + 14), (x0 + 42, y0 + 14),
                     (x0 + 18, y0 + 44), (x0 + 42, y0 + 44)]:
        draw.ellipse([lx, ly, lx + 6, ly + 6], fill=shade(WOOD, 0.7))


# 13 — chair
def tile_chair(x0, y0, rnd):
    noisy(draw, x0 + 18, y0 + 14, TILE - 36, TILE - 22, WOOD, jitter=8, seed=13)
    draw.ellipse([x0 + 18, y0 + 50, x0 + 46, y0 + 58], fill=(0, 0, 0, 60))
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


# 14 — crate 2
def tile_crate2(x0, y0, rnd):
    noisy(draw, x0 + 8, y0 + 8, TILE - 16, TILE - 16, WOOD, jitter=10, seed=14)
    draw.rectangle([x0 + 8, y0 + 8, x0 + 56, y0 + 56], fill=shade(WOOD, 0.7))
    draw.rectangle([x0 + 10, y0 + 10, x0 + 54, y0 + 54], fill=WOOD)
    # X cross-brace on the crate
    draw.line([x0 + 10, y0 + 10, x0 + 54, y0 + 54], fill=BLACK, width=2)
    draw.line([x0 + 54, y0 + 10, x0 + 10, y0 + 54], fill=BLACK, width=2)
    # plank lines
    for i in range(1, 5):
        y = y0 + 10 + i * 9
        draw.line([x0 + 12, y, x0 + 52, y], fill=shade(WOOD, 0.85), width=1)
    # metal corners
    for (cx, cy) in [(x0 + 8, y0 + 8), (x0 + 46, y0 + 8),
                     (x0 + 8, y0 + 46), (x0 + 46, y0 + 46)]:
        draw.rectangle([cx, cy, cx + 10, cy + 10], fill=RUST)
        draw.rectangle([cx, cy, cx + 10, cy + 10], outline=RUST_HI, width=1)
    draw.ellipse([x0 + 10, y0 + 56, x0 + 54, y0 + 58], fill=(0, 0, 0, 60))


# 15 — barrel 2
def tile_barrel2(x0, y0, rnd):
    noisy(draw, x0 + 16, y0 + 8, TILE - 32, TILE - 16, WOOD, jitter=10, seed=15)
    cx = x0 + TILE // 2
    # standing barrel
    draw.ellipse([x0 + 16, y0 + 8, x0 + 48, y0 + 58], fill=shade(WOOD, 0.85))
    for i in range(6):
        sx = x0 + 18 + i * 5
        draw.line([sx, y0 + 10, sx, y0 + 56], fill=shade(WOOD, 0.8), width=2)
    # hoops
    for y in (y0 + 14, y0 + 32, y0 + 50):
        draw.line([x0 + 16, y, x0 + 48, y], fill=RUST, width=3)
    # rim
    draw.ellipse([x0 + 16, y0 + 6, x0 + 48, y0 + 16], fill=shade(WOOD, 1.1))
    draw.ellipse([x0 + 18, y0 + 8, x0 + 46, y0 + 14], fill=shade(WOOD, 0.6))
    # tar patch
    draw.ellipse([x0 + 24, y0 + 26, x0 + 40, y0 + 40], fill=shade(BLACK, 1.4))
    # a crack
    draw.line([cx, y0 + 10, cx - 4, y0 + 22], fill=BLACK, width=1)
    draw.ellipse([x0 + 18, y0 + 58, x0 + 50, y0 + 62], fill=(0, 0, 0, 70))


TILES = [
    tile_planks, tile_wall, tile_crate, tile_barrel,
    tile_stall, tile_water, tile_sand, tile_rope,
    tile_lantern, tile_shadow, tile_rubble, tile_net,
    tile_table, tile_chair, tile_crate2, tile_barrel2,
]

# Per-tile properties: collision for solid objects, water for the pool.
PROPERTIES = {
    1: {"type": "wall", "collision": "true"},
    2: {"type": "crate", "collision": "true"},
    3: {"type": "barrel", "collision": "true"},
    4: {"type": "stall", "collision": "true"},
    5: {"type": "water", "collision": "false"},
    6: {"type": "sand"},
    7: {"type": "rope"},
    8: {"type": "lantern"},
    9: {"type": "shadow"},
    10: {"type": "rubble"},
    11: {"type": "net"},
    12: {"type": "table"},
    13: {"type": "chair"},
    14: {"type": "crate2", "collision": "true"},
    15: {"type": "barrel2", "collision": "true"},
}


def write_tsx():
    """Emit a Tiled .tsx tileset definition matching port_tileset.png."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<tileset version="1.10" name="port_tileset" '
        'tilewidth="64" tileheight="64" '
        'tilecount="%d" columns="%d" rows="%d">' % (COLS * ROWS, COLS, ROWS),
        '  <image source="port_tileset.png" width="256" height="256"/>',
    ]
    for idx, props in PROPERTIES.items():
        lines.append('  <tile id="%d">' % idx)
        for key, val in props.items():
            lines.append('    <property name="%s" value="%s"/>' % (key, val))
        lines.append('  </tile>')
    lines.append('</tileset>')
    text = "\n".join(lines) + "\n"
    with open(OUT_TSX, "w") as fh:
        fh.write(text)
    print("Successfully generated %s: %d tiles with properties."
          % (os.path.basename(OUT_TSX), len(PROPERTIES)))


def main():
    rnd = Random(2026)
    for idx, fn in enumerate(TILES):
        col = idx % COLS
        row = idx // COLS
        x0, y0 = cell(col, row)
        fn(x0, y0, rnd)
    img.save(OUT_PNG)
    print("Successfully generated %s (%dx%d): 16 tiles (4x4)."
          % (os.path.basename(OUT_PNG), WIDTH, HEIGHT))
    write_tsx()


main()
