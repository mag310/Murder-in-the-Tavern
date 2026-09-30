import os
import math
from PIL import Image, ImageDraw, ImageFilter
from random import Random

# --- Rego Cadere district tileset (Westcrown ruins after Aroden's fall). ---
# 256x192 spritesheet, 4 cols x 3 rows of 64x64 tiles (id 0..11).
# Style: abandoned district, ruins after the fall of Aroden.
# Palette: faded grey stone, dark green moss, rust-brown wood, murky blue.
# Atmosphere: dampness, decay, ruin. Perlin-style noise for stone texture.
TILE = 64
COLS = 4
ROWS = 3
WIDTH = TILE * COLS   # 256 px
HEIGHT = TILE * ROWS  # 192 px

# Strict per-tile clipping: each tile only touches its own 64x64 cell,
# so nothing ever bleeds into a neighbouring tile.
img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Output overwrites the existing tileset in ../maps/.
OUT_PNG = os.path.join(os.path.dirname(__file__), "..", "maps", "rego_cader_tileset.png")
OUT_TSX = os.path.join(os.path.dirname(__file__), "..", "maps", "rego_cader_tileset.tsx")


def shade(c, f):
    """Multiply an RGB(A) tuple by a factor (clip to 0..255)."""
    out = [max(0, min(255, int(v * f))) for v in c[:3]]
    if len(c) == 4:
        out.append(c[3])
    return tuple(out)


def perlin(d, x0, y0, w, h, base, jitter=14, scale=10, seed=None, extra=0):
    """Coarse low-frequency value-noise (chunky blotches) over `base`."""
    rnd = Random(seed)
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            f = 1.0 + rnd.uniform(-jitter / 100.0, jitter / 100.0)
            d.point((x, y), fill=shade(base, f))
    if extra:
        # second pass: finer grain so the stone doesn't look uniform
        rnd2 = Random((seed or 0) + 7000)
        for y in range(y0, y0 + h, 1):
            for x in range(x0, x0 + w, 1):
                f = 1.0 + rnd2.uniform(-extra / 100.0, extra / 100.0)
                d.point((x, y), fill=shade(base, f))


# --- Palettes (Westcrown ruins) ---
STONE = (98, 98, 102)        # faded grey stone
STONE_HI = (144, 144, 150)
STONE_DK = (56, 56, 62)
MOSS = (56, 80, 48)          # dark green moss
MOSS_HI = (92, 118, 70)
WOOD = (92, 64, 44)         # rust-brown wood
WOOD_HI = (140, 100, 70)
WOOD_DK = (52, 36, 26)
MURKY = (52, 64, 66)        # murky green-brown water
MURKY_HI = (86, 104, 94)
MUD = (72, 58, 42)          # dark brown dirt / mud
MUD_HI = (100, 80, 58)
RUST = (128, 86, 64)        # rust
RUST_HI = (176, 134, 100)
OKER = (168, 140, 92)       # faded ochre (thieves' mark)
DARKRED = (88, 40, 40)
BLUE = (52, 64, 92)        # muted blue
BLACK = (24, 24, 28)


def cell(col, row):
    return (col * TILE, row * TILE)


# ---- helpers that clip strictly to a cell (x0,y0,64,64) ----

def stone_base(d, x0, y0, seed):
    """Faded grey stone: Perlin noise + finer grain + a few cracks."""
    perlin(d, x0, y0, TILE, TILE, STONE, jitter=12, seed=seed, extra=6)
    rnd = Random(seed + 11)
    for _ in range(9):
        cx = x0 + rnd.randint(2, TILE - 4)
        cy = y0 + rnd.randint(2, TILE - 4)
        draw_line(d, [cx, cy, cx + rnd.randint(-8, 8), cy + rnd.randint(-8, 8)],
                  shade(STONE_DK, 1.0), 1)


def draw_line(d, pts, fill, width=1):
    """Line clipped to the current cell region."""
    d.line(pts, fill=fill, width=width)


def moss_patch(d, x0, y0, rnd, alpha_layer=None):
    """Blurred green moss blob drawn as an alpha overlay."""
    if alpha_layer is None:
        light = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    else:
        light = alpha_layer
    ld = ImageDraw.Draw(light)
    px = x0 + rnd.randint(2, TILE - 10)
    py = y0 + rnd.randint(2, TILE - 10)
    s = rnd.randint(6, 14)
    ld.ellipse([px, py, px + s, py + s], fill=shade(MOSS, rnd.uniform(0.8, 1.2)))
    return light


# =====================================================================
#  TILES
# =====================================================================

# 0 — cobblestone_ruined [passable]
def tile_cobble(x0, y0, rnd):
    perlin(draw, x0, y0, TILE, TILE, STONE, jitter=14, seed=0, extra=8)
    # cobble stones (offset rows), dark grime in the joints
    for row in range(5):
        y = y0 + row * 14
        off = 8 if row % 2 else 0
        for i in range(5):
            sx = x0 + i * 14 + off
            draw.ellipse([sx - 7, y - 6, sx + 7, y + 8], fill=shade(STONE, 1.06))
            draw.ellipse([sx - 7, y - 6, sx + 7, y + 8], outline=STONE_DK, width=1)
    # cracks
    for _ in range(9):
        cx = x0 + rnd.randint(0, TILE - 1)
        cy = y0 + rnd.randint(0, TILE - 1)
        draw_line(draw, [cx, cy, cx + rnd.randint(-8, 8), cy + rnd.randint(-8, 8)],
                  BLACK, 1)
    # potholes
    for _ in range(7):
        px = x0 + rnd.randint(2, TILE - 12)
        py = y0 + rnd.randint(2, TILE - 12)
        draw.ellipse([px, py, px + rnd.randint(6, 12), py + rnd.randint(6, 12)],
                     fill=shade(STONE, 0.45))
    # moss in a couple of joints
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    for _ in range(3):
        moss_patch(draw, x0, y0, rnd, alpha_layer=layer)
    layer = layer.filter(ImageFilter.GaussianBlur(2))
    img.alpha_composite(layer)


# 1 — dirt_mud [passable]
def tile_mud(x0, y0, rnd):
    perlin(draw, x0, y0, TILE, TILE, MUD, jitter=12, seed=1, extra=6)
    # wet dark stains
    for _ in range(10):
        px = x0 + rnd.randint(0, TILE - 16)
        py = y0 + rnd.randint(0, TILE - 16)
        draw.ellipse([px, py, px + rnd.randint(8, 16), py + rnd.randint(8, 16)],
                     fill=shade(MUD, 0.5))
    # grit / small stones
    for _ in range(28):
        px = x0 + rnd.randint(0, TILE - 4)
        py = y0 + rnd.randint(0, TILE - 4)
        draw.ellipse([px, py, px + rnd.randint(2, 5), py + rnd.randint(2, 5)],
                     fill=shade(MUD, rnd.choice((0.7, 1.2))))
    # rotten leaves (dark)
    for _ in range(8):
        px = x0 + rnd.randint(2, TILE - 12)
        py = y0 + rnd.randint(2, TILE - 12)
        draw.ellipse([px, py, px + rnd.randint(6, 11), py + rnd.randint(4, 8)],
                     fill=shade(MOSS, rnd.uniform(0.6, 0.9)))
    # wet sheen streak
    draw_line(draw, [x0 + 8, y0 + 40, x0 + 48, y0 + 52], shade(MUD, 1.25), 2)


# 2 — wall_crumbled [collision]
def tile_wall(x0, y0, rnd):
    perlin(draw, x0, y0, TILE, TILE, STONE_DK, jitter=12, seed=2, extra=6)
    bw, bh = 30, 14
    for row in range(5):
        y = y0 + row * 13
        off = 15 if row % 2 else 0
        for i in range(-1, 3):
            bx = x0 + i * bw + off
            if rnd.random() < 0.14:   # a crumbled-away block
                continue
            draw.rectangle([bx, y, bx + bw, y + bh], fill=shade(STONE, 1.0))
            draw.rectangle([bx, y, bx + bw, y + bh], outline=BLACK, width=1)
            draw_line(draw, [bx, y + 1, bx + bw, y + 1], shade(STONE_HI, 0.6), 1)
    # big cracks
    for _ in range(3):
        cx = x0 + rnd.randint(10, TILE - 20)
        draw_line(draw, [cx, y0, cx + rnd.randint(-10, 10), y0 + TILE], BLACK, 2)
    # damp streaks + moss in the lower part
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    for _ in range(5):
        px = x0 + rnd.randint(4, TILE - 12)
        py = y0 + TILE - 26 + rnd.randint(0, 12)
        draw.ellipse([px, py, px + rnd.randint(8, 16), py + rnd.randint(6, 12)],
                     fill=shade(MOSS, rnd.uniform(0.7, 1.1)))
        # drip
        draw_line(draw, [px + 4, py, px + 4, py + rnd.randint(8, 16)],
                  shade(MURKY, 0.7), 1)
    layer = layer.filter(ImageFilter.GaussianBlur(2))
    img.alpha_composite(layer)


# 3 — wall_window_boarded [collision]
def tile_window(x0, y0, rnd):
    perlin(draw, x0, y0, TILE, TILE, STONE, jitter=12, seed=3, extra=6)
    # stone joints
    for row in range(5):
        y = y0 + row * 13
        off = 15 if row % 2 else 0
        for i in range(-1, 3):
            bx = x0 + i * 30 + off
            draw.rectangle([bx, y, bx + 30, y + 13], outline=BLACK, width=1)
    # window opening (dark)
    wx, wy = x0 + 14, y0 + 12
    ww, wh = 36, 40
    draw.rectangle([wx, wy, wx + ww, wy + wh], fill=shade(BLACK, 1.4))
    draw.rectangle([wx, wy, wx + ww, wy + wh], outline=STONE_DK, width=2)
    # board planks across the window
    for i in range(5):
        px = x0 + 12 + i * 8
        draw.rectangle([px, wy - 2, px + 7, wy + wh + 2], fill=shade(WOOD_DK, 1.0))
        draw_line(draw, [px + 1, wy - 2, px + 1, wy + wh + 2], shade(WOOD, 0.6), 1)
    # X cross-brace (rotten boards)
    draw_line(draw, [wx, wy, wx + ww, wy + wh], shade(WOOD, 0.9), 3)
    draw_line(draw, [wx + ww, wy, wx, wy + wh], shade(WOOD, 0.85), 3)
    # nails
    for _ in range(6):
        nx = x0 + rnd.randint(16, 48)
        ny = y0 + rnd.randint(14, 50)
        draw.ellipse([nx, ny, nx + 2, ny + 2], fill=RUST)
    # moss in the lower corner
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    for _ in range(3):
        moss_patch(draw, x0, y0, rnd, alpha_layer=layer)
    layer = layer.filter(ImageFilter.GaussianBlur(2))
    img.alpha_composite(layer)


# 4 — wall_door_barricaded [collision]
def tile_door(x0, y0, rnd):
    perlin(draw, x0, y0, TILE, TILE, STONE, jitter=12, seed=4, extra=6)
    # stone joints
    for row in range(5):
        y = y0 + row * 13
        off = 15 if row % 2 else 0
        for i in range(-1, 3):
            bx = x0 + i * 30 + off
            draw.rectangle([bx, y, bx + 30, y + 13], outline=BLACK, width=1)
    # door (dark, cracked wood)
    dx, dy = x0 + 16, y0 + 10
    dw, dh = 32, 48
    draw.rectangle([dx, dy, dx + dw, dy + dh], fill=shade(WOOD_DK, 1.0))
    draw.rectangle([dx, dy, dx + dw, dy + dh], outline=BLACK, width=2)
    for g in range(1, 4):
        draw_line(draw, [dx, dy + g * 12, dx + dw, dy + g * 12],
                  shade(WOOD_DK, 0.7), 1)
    # barricade: stacked furniture + boards piled in front
    # a tipped chair/box
    draw.rectangle([x0 + 6, y0 + 30, x0 + 30, y0 + 54], fill=shade(WOOD, 0.85))
    draw.rectangle([x0 + 6, y0 + 30, x0 + 30, y0 + 54], outline=BLACK, width=1)
    draw_line(draw, [x0 + 8, y0 + 36, x0 + 28, y0 + 40], shade(WOOD_DK, 0.7), 1)
    # leaning boards
    draw_line(draw, [x0 + 30, y0 + 56, x0 + 48, y0 + 16], shade(WOOD, 0.9), 4)
    draw_line(draw, [x0 + 34, y0 + 56, x0 + 52, y0 + 24], shade(WOOD, 0.8), 3)
    # a barrel jammed in
    draw.ellipse([x0 + 36, y0 + 34, x0 + 54, y0 + 56], fill=shade(WOOD_DK, 1.0))
    draw_line(draw, [x0 + 36, y0 + 44, x0 + 54, y0 + 44], shade(RUST, 0.6), 2)
    # splinters
    for _ in range(10):
        px = x0 + rnd.randint(6, TILE - 8)
        py = y0 + rnd.randint(28, TILE - 6)
        draw_line(draw, [px, py, px + rnd.randint(3, 9), py + rnd.randint(-3, 3)],
                  shade(WOOD, 1.1), 1)
    # nails sticking out
    for _ in range(6):
        nx = x0 + rnd.randint(10, TILE - 6)
        ny = y0 + rnd.randint(20, TILE - 6)
        draw.ellipse([nx, ny, nx + 2, ny + 2], fill=RUST)


# 5 — barricade_wood [collision]
def tile_barricade(x0, y0, rnd):
    perlin(draw, x0, y0, TILE, TILE, MUD, jitter=8, seed=5, extra=6)
    # a tipped-over cart bed (tilted)
    draw.polygon([(x0 + 8, y0 + 34), (x0 + 52, y0 + 26),
                  (x0 + 56, y0 + 46), (x0 + 6, y0 + 52)], fill=shade(WOOD, 0.9))
    draw.polygon([(x0 + 8, y0 + 34), (x0 + 52, y0 + 26),
                  (x0 + 56, y0 + 46), (x0 + 6, y0 + 52)], outline=BLACK, width=1)
    for i in range(1, 4):
        draw_line(draw, [x0 + 12 + i * 10, y0 + 28, x0 + 12 + i * 10, y0 + 50],
                  shade(WOOD_DK, 0.7), 1)
    # wheel
    draw.ellipse([x0 + 10, y0 + 48, x0 + 30, y0 + 62], fill=shade(WOOD_DK, 1.2))
    draw.ellipse([x0 + 12, y0 + 50, x0 + 28, y0 + 60], fill=BLACK)
    # stacked planks
    for i in range(4):
        py = y0 + 12 + i * 5
        draw.rectangle([x0 + 30, py, x0 + 58, py + 4], fill=shade(WOOD, 0.85))
        draw_line(draw, [x0 + 30, py + 1, x0 + 58, py + 1], shade(WOOD_DK, 0.7), 1)
    # a barrel
    draw.ellipse([x0 + 38, y0 + 30, x0 + 56, y0 + 50], fill=shade(WOOD_DK, 1.0))
    draw_line(draw, [x0 + 38, y0 + 38, x0 + 56, y0 + 38], shade(RUST, 0.6), 2)
    # a crate
    draw.rectangle([x0 + 4, y0 + 14, x0 + 22, y0 + 32], fill=shade(WOOD, 0.95))
    draw.rectangle([x0 + 4, y0 + 14, x0 + 22, y0 + 32], outline=BLACK, width=1)
    # sticking-out nails + splinters
    for _ in range(12):
        px = x0 + rnd.randint(6, TILE - 8)
        py = y0 + rnd.randint(12, TILE - 6)
        draw_line(draw, [px, py, px + rnd.randint(2, 6), py + rnd.randint(-3, 3)],
                  shade(RUST_HI, 0.8), 1)
    # a few gunk spots
    for _ in range(5):
        px = x0 + rnd.randint(4, TILE - 10)
        py = y0 + rnd.randint(10, TILE - 8)
        draw.ellipse([px, py, px + rnd.randint(4, 9), py + rnd.randint(4, 9)],
                     fill=shade(WOOD_DK, 0.6))
    shadow_pool(x0, y0, 6, 58, 56, 62, alpha=55)


# 6 — rubble_passable [passable]
def tile_rubble(x0, y0, rnd):
    perlin(draw, x0, y0, TILE, TILE, MUD, jitter=10, seed=6, extra=6)
    # heap of stones / gravel
    for _ in range(26):
        px = x0 + rnd.randint(2, TILE - 16)
        py = y0 + rnd.randint(4, TILE - 8)
        c = rnd.choice([STONE, STONE_DK, MUD, WOOD_DK])
        s = rnd.randint(6, 16)
        draw.ellipse([px, py, px + s, py + s], fill=shade(c, rnd.uniform(0.7, 1.1)))
    # angular broken blocks
    for _ in range(8):
        px = x0 + rnd.randint(4, TILE - 22)
        py = y0 + rnd.randint(8, TILE - 16)
        draw.polygon([(px, py), (px + rnd.randint(8, 18), py),
                      (px + rnd.randint(6, 16), py + rnd.randint(8, 14)),
                      (px + rnd.randint(0, 8), py + rnd.randint(10, 16))],
                     fill=shade(STONE, rnd.uniform(0.7, 1.1)))
    # a couple of rotted planks
    for _ in range(3):
        px = x0 + rnd.randint(4, TILE - 26)
        py = y0 + rnd.randint(6, TILE - 12)
        draw.rectangle([px, py, px + rnd.randint(14, 26), py + rnd.randint(4, 7)],
                       fill=shade(WOOD_DK, 1.0))
    # rags / cloth
    for _ in range(4):
        px = x0 + rnd.randint(4, TILE - 16)
        py = y0 + rnd.randint(6, TILE - 12)
        draw.polygon([(px, py), (px + 12, py + 2), (px + 8, py + 12),
                       (px + 2, py + 10)], fill=shade(DARKRED, 0.7))
    # moss specks
    for _ in range(4):
        px = x0 + rnd.randint(4, TILE - 8)
        py = y0 + rnd.randint(4, TILE - 8)
        draw.ellipse([px, py, px + 6, py + 6], fill=shade(MOSS, 0.9))


# 7 — puddle [passable]
def tile_puddle(x0, y0, rnd):
    perlin(draw, x0, y0, TILE, TILE, MUD, jitter=8, seed=7)
    # the puddle (murky, mostly lower half)
    draw.ellipse([x0 + 6, y0 + 26, x0 + 58, y0 + 60], fill=shade(MURKY, 1.0))
    draw.ellipse([x0 + 10, y0 + 30, x0 + 54, y0 + 58], fill=shade(MURKY, 0.85))
    # ripples
    for _ in range(14):
        rx = x0 + rnd.randint(8, 52)
        ry = y0 + rnd.randint(34, 58)
        rw = rnd.randint(3, 11)
        draw_line(draw, [rx, ry, rx + rw, ry], shade(MURKY_HI, 0.9), 1)
    # duckweed / algae clumps at the edges
    for _ in range(16):
        px = x0 + rnd.randint(8, 52)
        py = y0 + rnd.randint(30, 58)
        draw.ellipse([px, py, px + rnd.randint(3, 7), py + rnd.randint(3, 7)],
                     fill=shade(MOSS, rnd.uniform(0.7, 1.2)))
    # dull glints
    for _ in range(5):
        gx = x0 + rnd.randint(12, 50)
        gy = y0 + rnd.randint(34, 56)
        draw.point((gx, gy), fill=shade(MURKY_HI, 1.7))
    # damp rim
    draw.ellipse([x0 + 6, y0 + 26, x0 + 58, y0 + 60], outline=shade(MURKY, 0.5), width=2)


# 8 — shadow [passable]
def tile_shadow(x0, y0, rnd):
    light = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    sd = ImageDraw.Draw(light)
    # uneven blob, not a clean ellipse
    for _ in range(24):
        cx = x0 + rnd.randint(8, 56)
        cy = y0 + rnd.randint(14, 56)
        s = rnd.randint(6, 18)
        sd.ellipse([cx - s, cy - s, cx + s, cy + s], fill=(20, 20, 24, rnd.randint(70, 140)))
    light = light.filter(ImageFilter.GaussianBlur(4))
    img.alpha_composite(light)


# 9 — thieves_mark [passable]
def tile_mark(x0, y0, rnd):
    perlin(draw, x0, y0, TILE, TILE, STONE, jitter=12, seed=9, extra=6)
    # cracks
    for _ in range(5):
        cx = x0 + rnd.randint(0, TILE - 1)
        cy = y0 + rnd.randint(0, TILE - 1)
        draw_line(draw, [cx, cy, cx + rnd.randint(-6, 6), cy + rnd.randint(-6, 6)],
                  shade(STONE_DK, 1.0), 1)
    # chalked thieves' mark: stylised eye + trident, faded ochre
    ink = shade(OKER, 0.9)
    cx, cy = x0 + 32, y0 + 32
    # eye almond
    draw.chord([cx - 18, cy - 12, cx + 18, cy + 12], -20, 20, outline=ink, width=2)
    # pupil
    draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=ink)
    draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=BLACK)
    # trident prongs above the eye
    for dx in (-9, 0, 9):
        draw_line(draw, [cx + dx, cy - 12, cx + dx, cy - 26], ink, 2)
    draw_line(draw, [cx - 9, cy - 26, cx + 9, cy - 26], ink, 2)
    # worn edge
    draw.ellipse([x0 + 8, y0 + 10, x0 + 56, y0 + 56], outline=shade(ink, 0.5), width=1)


# 10 — wall_vine [collision]
def tile_vine_wall(x0, y0, rnd):
    perlin(draw, x0, y0, TILE, TILE, STONE_DK, jitter=12, seed=10, extra=6)
    # stone blocks
    bw, bh = 30, 14
    for row in range(5):
        y = y0 + row * 13
        off = 15 if row % 2 else 0
        for i in range(-1, 3):
            bx = x0 + i * bw + off
            draw.rectangle([bx, y, bx + bw, y + bh], fill=shade(STONE, 1.0))
            draw.rectangle([bx, y, bx + bw, y + bh], outline=BLACK, width=1)
    # ivy vine trunks
    for _ in range(6):
        vx = x0 + rnd.randint(6, TILE - 8)
        draw_line(draw, [vx, y0, vx + rnd.randint(-8, 8), y0 + TILE],
                  shade(MOSS, 1.1), 2)
    # leaf clusters
    for _ in range(60):
        px = x0 + rnd.randint(2, TILE - 8)
        py = y0 + rnd.randint(2, TILE - 8)
        draw.ellipse([px, py, px + rnd.randint(4, 9), py + rnd.randint(4, 9)],
                     fill=shade(MOSS, rnd.uniform(0.7, 1.3)))
    # lighter highlights
    for _ in range(18):
        px = x0 + rnd.randint(2, TILE - 6)
        py = y0 + rnd.randint(2, TILE - 6)
        draw.ellipse([px, py, px + 5, py + 5], fill=shade(MOSS_HI, 0.9))
    # hanging tendrils
    for _ in range(6):
        vx = x0 + rnd.randint(4, TILE - 6)
        draw_line(draw, [vx, y0, vx + rnd.randint(-3, 3), y0 + rnd.randint(8, 24)],
                  shade(MOSS, 1.0), 1)


# 11 — debris_wood [collision]
def tile_debris(x0, y0, rnd):
    perlin(draw, x0, y0, TILE, TILE, MUD, jitter=10, seed=11, extra=6)
    # rotten planks / beams
    for _ in range(7):
        px = x0 + rnd.randint(2, TILE - 28)
        py = y0 + rnd.randint(4, TILE - 10)
        c = rnd.choice([WOOD_DK, WOOD, shade(WOOD_DK, 1.3)])
        pw = rnd.randint(14, 30)
        draw.rectangle([px, py, px + pw, py + rnd.randint(5, 9)],
                       fill=shade(c, rnd.uniform(0.7, 1.1)))
        draw.rectangle([px, py, px + pw, py + rnd.randint(5, 9)], outline=BLACK, width=1)
        for g in range(2):
            draw_line(draw, [px, py + 2 + g * 3, px + pw, py + 2 + g * 3],
                     shade(c, 0.7), 1)
    # splinters
    for _ in range(20):
        px = x0 + rnd.randint(2, TILE - 6)
        py = y0 + rnd.randint(2, TILE - 4)
        draw_line(draw, [px, py, px + rnd.randint(3, 10), py + rnd.randint(-3, 3)],
                  shade(WOOD, rnd.uniform(0.8, 1.2)), 1)
    # broken beam (broken in the middle)
    draw_line(draw, [x0 + 4, y0 + 20, x0 + 30, y0 + 22], shade(WOOD_DK, 1.0), 5)
    draw_line(draw, [x0 + 34, y0 + 18, x0 + 60, y0 + 14], shade(WOOD_DK, 0.9), 5)
    # gunk spots
    for _ in range(5):
        px = x0 + rnd.randint(4, TILE - 8)
        py = y0 + rnd.randint(4, TILE - 8)
        draw.ellipse([px, py, px + 6, py + 6], fill=shade(WOOD_DK, 0.6))
    # moss on a plank
    for _ in range(5):
        px = x0 + rnd.randint(4, TILE - 8)
        py = y0 + rnd.randint(4, TILE - 8)
        draw.ellipse([px, py, px + 6, py + 6], fill=shade(MOSS, 0.9))


def shadow_pool(x0, y0, rx1, rx2, ry1, ry2, alpha=60):
    """Soft ground shadow within the cell."""
    light = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ld = ImageDraw.Draw(light)
    ld.ellipse([x0 + rx1, y0 + ry1, x0 + rx2, y0 + ry2], fill=(0, 0, 0, alpha))
    light = light.filter(ImageFilter.GaussianBlur(3))
    img.alpha_composite(light)


# =====================================================================
#  LAYOUT
# =====================================================================

TILES = [
    tile_cobble, tile_mud, tile_wall, tile_window,
    tile_door, tile_barricade, tile_rubble, tile_puddle,
    tile_shadow, tile_mark, tile_vine_wall, tile_debris,
]

# collision=true for tiles 2,3,4,5,10,11; passable (no collision) for the rest.
PROPERTIES = {
    0: {"type": "cobblestone_ruined"},
    1: {"type": "dirt_mud"},
    2: {"type": "wall_crumbled", "collision": "true"},
    3: {"type": "wall_window_boarded", "collision": "true"},
    4: {"type": "wall_door_barricaded", "collision": "true"},
    5: {"type": "barricade_wood", "collision": "true"},
    6: {"type": "rubble_passable"},
    7: {"type": "puddle"},
    8: {"type": "shadow"},
    9: {"type": "thieves_mark"},
    10: {"type": "wall_vine", "collision": "true"},
    11: {"type": "debris_wood", "collision": "true"},
}


def write_tsx():
    """Emit a Tiled .tsx tileset definition matching rego_cader_tileset.png."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<tileset version="1.10" name="rego_cader_tileset" '
        'tilewidth="64" tileheight="64" '
        'tilecount="%d" columns="%d" rows="%d">' % (COLS * ROWS, COLS, ROWS),
        '  <image source="rego_cader_tileset.png" width="256" height="192"/>',
    ]
    for idx in range(COLS * ROWS):
        props = PROPERTIES.get(idx, {})
        lines.append('  <tile id="%d">' % idx)
        lines.append('    <properties>')
        for key, val in props.items():
            lines.append('      <property name="%s" value="%s"/>' % (key, val))
        lines.append('    </properties>')
        lines.append('  </tile>')
    lines.append('</tileset>')
    with open(OUT_TSX, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    ncol = sum(1 for p in PROPERTIES.values() if "collision" in p)
    print("Successfully generated %s: %d tiles (collision=%d, passable=%d)."
          % (os.path.basename(OUT_TSX), COLS * ROWS, ncol, COLS * ROWS - ncol))


def main():
    rnd = Random(2026)
    for idx, fn in enumerate(TILES):
        col = idx % COLS
        row = idx // COLS
        x0, y0 = cell(col, row)
        fn(x0, y0, rnd)
    img.save(OUT_PNG)
    print("Successfully generated %s (%dx%d): %d tiles (%dx%d grid)."
          % (os.path.basename(OUT_PNG), WIDTH, HEIGHT, COLS * ROWS, COLS, ROWS))
    write_tsx()


main()
