from PIL import Image, ImageDraw, ImageFont
from random import Random, uniform, randint

# --- Bladewing Bridge battlemap generator (TMX geometry) ---
# 24 x 12 grid at 32 px/cell  ->  768 x 384 (matches bladewing_bridge.tmx).
CELL = 32
COLS, ROWS = 24, 12
WIDTH = CELL * COLS    # 768
HEIGHT = CELL * ROWS   # 384

img = Image.new("RGBA", (WIDTH, HEIGHT), color=(25, 45, 75, 255))
draw = ImageDraw.Draw(img)


def shade(c, f):
    """Multiply an RGB(a) colour by a factor (clip to 0..255)."""
    out = [max(0, min(255, int(v * f))) for v in c[:3]]
    if len(c) == 4:
        out.append(c[3])
    return tuple(out)


def noisy(d, x0, y0, w, h, base, jitter=10, seed=None):
    """Per-pixel value noise (grain) around an RGB(a) colour."""
    rnd = Random(seed)
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            f = 1.0 + rnd.uniform(-jitter / 100.0, jitter / 100.0)
            d.point((x, y), fill=shade(base, f))


# --- Palette (matches the existing hand-authored battlemap) ---
WATER = (25, 45, 75)
WATER_HI = (34, 100, 203)
BANK = (115, 95, 75)
STONE = (105, 110, 115)
PARAPET = (50, 50, 50)
J = (90, 95, 100)


# 1. WATER (channel) — whole canvas base
noisy(draw, 0, 0, WIDTH, HEIGHT, WATER, jitter=10, seed=1)
# horizontal ripple streaks across the channel
for _ in range(90):
    x = randint(0, WIDTH - 30)
    y = randint(0, HEIGHT - 1)
    draw.line([x, y, x + randint(10, 26), y], fill=WATER_HI, width=1)
    draw.line([x + 2, y + 2, x + 9, y + 2], fill=(30, 90, 180), width=1)
# foam specks
for _ in range(140):
    draw.point((randint(0, WIDTH - 1), randint(0, HEIGHT - 1)), fill=WATER_HI)


# 2. BANKS (left / right land)
for bx0, bx1 in [(0, 3 * CELL), (17 * CELL, WIDTH)]:
    noisy(draw, bx0, 2 * CELL, bx1 - bx0, 6 * CELL, BANK, jitter=16, seed=2)
    # grass tufts + dirt along the water edge
    for _ in range(60):
        x = randint(bx0, bx1 - 1)
        y = 2 * CELL + randint(0, 6 * CELL - 1)
        draw.point((x, y), fill=shade(BANK, 0.7 + 0.6 * uniform(0, 1)))
    # a few grass blades on the bank
    for _ in range(20):
        x = randint(bx0, bx1 - 1)
        y = 2 * CELL + randint(0, 6 * CELL - 3)
        draw.line([x, y, x, y - 2], fill=(74, 96, 50), width=1)


# 3. STONE BRIDGE (center: cols 3..17, rows 2..8)
bridge_box = (3 * CELL, 2 * CELL, 17 * CELL, 8 * CELL)
bx0, by0, bx1, by1 = bridge_box
noisy(draw, bx0, by0, bx1 - bx0, by1 - by0, STONE, jitter=10, seed=3)
# parapet bands (top + bottom)
parapet_h = int(0.3 * CELL)
noisy(draw, bx0, by0, bx1 - bx0, parapet_h, PARAPET, jitter=10, seed=4)
noisy(draw, bx0, by1 - parapet_h, bx1 - bx0, parapet_h, PARAPET, jitter=10, seed=5)
# lighter coping on the parapet top edge
draw.line([bx0, by0, bx1, by0], fill=shade(PARAPET, 1.5), width=1)
draw.line([bx0, by1 - 1, bx1, by1 - 1], fill=shade(PARAPET, 1.5), width=1)
# flagstone joints on the deck (between parapets)
deck_y0 = by0 + parapet_h
deck_y1 = by1 - parapet_h
for x in range(bx0 + 2, bx1 - 1, 40):
    draw.line([x, deck_y0, x, deck_y1], fill=J, width=1)
for y in range(deck_y0, deck_y1, 40):
    draw.line([bx0, y, bx1, y], fill=J, width=1)
# a couple of dark cracks
draw.line([bx0 + 40, deck_y0 + 10, bx0 + 120, deck_y0 + 30, bx0 + 200, deck_y0 + 20],
          fill=shade(STONE, 0.5), width=1)
draw.line([bx0 + 300, deck_y0 + 40, bx0 + 420, deck_y0 + 30, bx0 + 520, deck_y0 + 45],
          fill=shade(STONE, 0.5), width=1)
# moss in the joints
for _ in range(30):
    x = randint(bx0, bx1 - 1)
    y = randint(deck_y0, deck_y1 - 1)
    draw.point((x, y), fill=(60, 84, 52))


# 4. PEGASUS STATUES on the 4 parapet corners (top-down, wings = swords)
def draw_pegasus_statue(cx, cy):
    """Top-down gothic stone pegasus: body, head, sword-wings."""
    stone = (160, 165, 170)
    stone_lo = shade(stone, 0.6)
    steel = (190, 196, 205)
    # ground shadow
    draw.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=(0, 0, 0, 60))
    # body
    draw.ellipse([cx - 20, cy - 25, cx + 20, cy + 25], fill=stone,
                 outline=stone_lo, width=2)
    # head (rearing, up)
    draw.ellipse([cx - 10, cy - 35, cx + 10, cy - 20], fill=stone)
    # mane (short strokes along the head/neck)
    for _ in range(4):
        draw.line([cx - randint(4, 8), cy - randint(22, 30),
                   cx - randint(6, 10), cy - randint(26, 32)],
                  fill=stone_lo, width=1)
    # left sword-wing
    draw.polygon([(cx - 15, cy - 10), (cx - 55, cy - 40), (cx - 20, cy + 5)],
                 fill=steel, outline=shade(steel, 0.5))
    # right sword-wing
    draw.polygon([(cx + 15, cy - 10), (cx + 55, cy - 40), (cx + 20, cy + 5)],
                 fill=steel, outline=shade(steel, 0.5))
    # glint
    draw.line([cx - 40, cy - 32, cx - 16, cy - 6], fill=shade(steel, 1.4), width=1)
    draw.line([cx + 40, cy - 32, cx + 16, cy - 6], fill=shade(steel, 1.4), width=1)
    # weathering cracks
    for _ in range(5):
        draw.point((cx + randint(-16, 16), cy + randint(-20, 20)), fill=stone_lo)


for px, py in [(3 * CELL + 40, 2 * CELL + 40), (3 * CELL + 40, 7 * CELL + 40),
               (16 * CELL + 40, 2 * CELL + 40), (16 * CELL + 40, 7 * CELL + 40)]:
    draw_pegasus_statue(px, py)


# 5. BARRICADE tokens (cover on the bridge) — wooden crates + chains + debris
def draw_barricade(cx, cy):
    wood = (110, 78, 46)
    wood_lo = shade(wood, 0.6)
    wood_hi = shade(wood, 1.25)
    iron = (120, 124, 132)
    stone = (120, 118, 110)
    # shadow
    draw.ellipse([cx - 16, cy + 14, cx + 16, cy + 24], fill=(0, 0, 0, 70))
    # stone debris behind
    for _ in range(4):
        sx = cx - 18 + randint(0, 36)
        sy = cy - 14 + randint(0, 10)
        draw.ellipse([sx, sy, sx + 8, sy + 8], fill=stone)
    # crates
    def crate(x, y, w, h):
        draw.rectangle([x, y, x + w, y + h], fill=wood)
        noisy(draw, x, y, w, h, wood, jitter=12, seed=randint(1, 9999))
        draw.rectangle([x, y, x + w, y + 2], fill=wood_hi)
        draw.rectangle([x, y + h - 2, x + w, y + h], fill=wood_lo)
        draw.line([x, y + h // 2, x + w, y + h // 2], fill=wood_lo, width=1)
        draw.line([x + w // 2, y, x + w // 2, y + h], fill=wood_lo, width=1)
    crate(cx - 16, cy + 4, 18, 18)
    crate(cx + 2, cy + 2, 16, 20)
    crate(cx - 6, cy - 10, 14, 12)
    # chains
    for _ in range(2):
        x = cx - 14 + randint(0, 28)
        y = cy - 12 + randint(0, 16)
        draw.ellipse([x, y, x + 4, y + 5], outline=iron, width=1)
    draw.line([cx - 12, cy - 8, cx + 4, cy + 4, cx + 16, cy - 2], fill=iron, width=1)


for bx, by in [(5 * CELL + 16, 4 * CELL + 16), (9 * CELL + 16, 5 * CELL + 16)]:
    draw_barricade(bx, by)


# 6. GUARD / LIEUTENANT tokens (from the Spawns object group in the TMX)
def draw_token(cx, cy, text, is_leader=False):
    color = (180, 50, 50, 255) if is_leader else (70, 100, 150, 255)
    border = (220, 200, 50, 255) if is_leader else (200, 200, 200, 255)
    # shadow
    draw.ellipse([cx - 23, cy + 18, cx + 23, cy + 28], fill=(0, 0, 0, 70))
    # token
    draw.ellipse([cx - 25, cy - 25, cx + 25, cy + 25], fill=color,
                 outline=border, width=3)
    # rim highlight
    draw.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], outline=shade(color, 1.3),
                 width=1)
    try:
        font = ImageFont.load_default()
        draw.text((cx - 12, cy - 6), text, fill=(255, 255, 255, 255), font=font)
    except Exception:
        draw.text((cx - 12, cy - 6), text, fill=(255, 255, 255, 255))


# positions from the TMX Spawns object group (top-left of 32x32 -> center)
def center(px, py):
    return px + CELL // 2, py + CELL // 2


draw_token(*center(256, 128), "G1")
draw_token(*center(256, 224), "G2")
draw_token(*center(384, 160), "L", is_leader=True)
draw_token(*center(544, 128), "G3")
draw_token(*center(544, 224), "G4")


# 7. GRID (faint, for TMX editing)
for x in range(0, WIDTH, CELL):
    draw.line([(x, 0), (x, HEIGHT)], fill=(255, 255, 255, 30), width=1)
for y in range(0, HEIGHT, CELL):
    draw.line([(0, y), (WIDTH, y)], fill=(255, 255, 255, 30), width=1)


img.save("bladewing_bridge_battlemap.png")
print("Successfully generated bladewing_bridge_battlemap.png (%dx%d)." % (WIDTH, HEIGHT))
