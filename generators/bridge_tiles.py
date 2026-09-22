from PIL import Image, ImageDraw, ImageFilter
import random

random.seed(7)

# Tileset specification — 128x32 px, 4 tiles of 32x32 each.
TILE = 32
WIDTH = TILE * 4   # 128 px
HEIGHT = TILE      # 32 px

# Palette (Dark Fantasy Style).
WATER = (30, 90, 180)    # Вода — синий/голубой
STONE = (128, 128, 128)  # Мост — серый камень
PARAPET = (60, 60, 60)   # Парапет — тёмно-серый
APPROACH = (139, 105, 70)  # Подход — коричневая земля/дорога


def shade(c, f):
    """Multiply an RGB tuple by a factor (clip to 0..255)."""
    return tuple(max(0, min(255, int(v * f))) for v in c)


def noisy_fill(d, x0, y0, w, h, base, jitter=10, seed=None):
    """Fill a rect with per-pixel value noise (grain) around `base`."""
    rnd = random.Random(seed)
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            f = 1.0 + rnd.uniform(-jitter / 100.0, jitter / 100.0)
            d.point((x, y), fill=shade(base, f))


def draw_water(d, x0, y0, w, h):
    """Water: blue base with wavy lighter streaks and a few foam specks."""
    noisy_fill(d, x0, y0, w, h, WATER, jitter=8, seed=1)
    for _ in range(4):
        y = y0 + random.randint(4, h - 6)
        x = x0 + random.randint(0, w - 14)
        d.line([x, y, x + random.randint(8, 14), y],
               fill=shade(WATER, 1.35), width=1)
        d.line([x + 2, y + 2, x + 9, y + 2],
               fill=shade(WATER, 1.15), width=1)
    for _ in range(10):
        x = x0 + random.randint(0, w - 1)
        y = y0 + random.randint(0, h - 1)
        d.point((x, y), fill=shade(WATER, 1.5))


def draw_stone(d, x0, y0, w, h):
    """Bridge: grey stone flagstones with mortar joints, cracks and moss."""
    noisy_fill(d, x0, y0, w, h, STONE, jitter=12, seed=2)
    # mortar joints (stone-laid flagstones), a vertical + a horizontal seam
    seam_x = x0 + w // 2
    seam_y = y0 + h // 2
    d.line([x0, seam_y, x0 + w, seam_y], fill=shade(STONE, 0.55), width=1)
    d.line([seam_x, y0, seam_x, y0 + h], fill=shade(STONE, 0.55), width=1)
    # a dark crack running across a couple of stones
    d.line([x0 + 4, y0 + 3, x0 + 10, y0 + 9, x0 + 8, y0 + 16,
            x0 + 12, y0 + 22], fill=shade(STONE, 0.5), width=1)
    # top-left sheen + bottom-right shadow
    d.line([x0, y0, x0 + w, y0], fill=shade(STONE, 1.2), width=1)
    d.line([x0, y0, x0, y0 + h], fill=shade(STONE, 1.15), width=1)
    d.line([x0, y0 + h - 1, x0 + w, y0 + h - 1], fill=shade(STONE, 0.8), width=1)
    d.line([x0 + w - 1, y0, x0 + w - 1, y0 + h], fill=shade(STONE, 0.8), width=1)
    # a little green moss in the joints
    for _ in range(5):
        x = x0 + random.randint(0, w - 1)
        y = y0 + random.randint(0, h - 1)
        d.point((x, y), fill=(60, 84, 52))


def draw_parapet(d, x0, y0, w, h):
    """Parapet: dark grey stone with a lighter coping on top and a cap band."""
    noisy_fill(d, x0, y0, w, h, PARAPET, jitter=10, seed=3)
    # top coping (a lighter cap band along the top edge)
    d.rectangle([x0, y0, x0 + w - 1, y0 + 3], fill=shade(PARAPET, 1.45))
    d.line([x0, y0 + 3, x0 + w, y0 + 3], fill=shade(PARAPET, 0.6), width=1)
    # a couple of vertical block joints
    for jx in (x0 + 8, x0 + 20):
        d.line([jx, y0 + 4, jx, y0 + h], fill=shade(PARAPET, 0.6), width=1)
    # weathering specks
    for _ in range(8):
        x = x0 + random.randint(0, w - 1)
        y = y0 + random.randint(4, h - 1)
        d.point((x, y), fill=shade(PARAPET, random.choice((0.6, 1.25))))


def draw_approach(d, x0, y0, w, h):
    """Approach: brown dirt/road with pebbles, grass tufts and a worn track."""
    noisy_fill(d, x0, y0, w, h, APPROACH, jitter=14, seed=4)
    # pebbles
    for _ in range(14):
        x = x0 + random.randint(0, w - 2)
        y = y0 + random.randint(0, h - 2)
        d.ellipse([x, y, x + 1, y + 1], fill=shade(APPROACH, random.choice((0.7, 1.3))))
    # a worn, lighter track across the middle
    for _ in range(3):
        y = y0 + random.randint(h // 2 - 4, h // 2 + 4)
        d.line([x0, y, x0 + w, y], fill=shade(APPROACH, 1.25), width=1)
    # grass tufts
    for _ in range(7):
        x = x0 + random.randint(0, w - 1)
        y = y0 + random.randint(0, h - 3)
        d.line([x, y, x, y - 2], fill=(74, 96, 50), width=1)
        d.line([x + 1, y, x + 1, y - 2], fill=(90, 112, 58), width=1)


def render():
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    tiles = [
        (draw_water, WATER),
        (draw_stone, STONE),
        (draw_parapet, PARAPET),
        (draw_approach, APPROACH),
    ]
    for i, (fn, color) in enumerate(tiles):
        x0 = i * TILE
        draw.rectangle([x0, 0, x0 + TILE - 1, HEIGHT - 1], fill=color)
        fn(draw, x0, 0, TILE, HEIGHT)
    # soft overall grain so nothing looks perfectly flat
    img = img.filter(ImageFilter.GaussianBlur(0.4))
    img.save("bridge_tiles.png")
    print("Successfully generated bridge_tiles.png (128x32) with textured water/bridge/parapet/approach.")


render()
