from PIL import Image, ImageDraw
from random import Random, randint, uniform

# --- Guard (Dottari) tileset, top-down tokens. ---
# Black background for easy transparency masking. 64x64 tiles.
# 4 tiles = the four near-independent divisions (Westcrown lore).
TILE = 64
COLS = 4
WIDTH = TILE * COLS  # 256 px
HEIGHT = TILE        # 64 px

img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)


def shade(c, f):
    """Multiply an RGB(a) tuple by a factor (clip to 0..255)."""
    out = [max(0, min(255, int(v * f))) for v in c[:3]]
    if len(c) == 4:
        out.append(c[3])
    return tuple(out)


def noisy(d, x0, y0, w, h, base, jitter=10, seed=None):
    rnd = Random(seed)
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            f = 1.0 + rnd.uniform(-jitter / 100.0, jitter / 100.0)
            d.point((x, y), fill=shade(base, f))


def draw_guard(idx, x0, y0, pal):
    """Top-down guard token: a uniformed soldier with a round shield and
    a long spear/halberd. Colour-coded by division."""
    left, top, right, bot = x0 + 4, y0 + 4, x0 + TILE - 5, y0 + TILE - 5
    rnd = Random(1000 + idx)
    cx = x0 + TILE // 2
    armor = pal["armor"]
    trim = pal["trim"]
    metal = (150, 156, 168)
    metal_lo = shade(metal, 0.6)
    skin = (196, 168, 132)

    # ground shadow
    d = draw
    d.ellipse([x0 + 16, y0 + 48, x0 + 48, y0 + 60], fill=(0, 0, 0, 90))

    # --- spear / halberd (behind, vertical, slightly to the right) ---
    sx = cx + 12
    d.rectangle([sx, y0 + 4, sx + 3, y0 + 56], fill=(96, 74, 48))   # shaft
    d.line([sx + 1, y0 + 4, sx + 1, y0 + 56], fill=shade((96, 74, 48), 1.2), width=1)
    # head (halberd: blade + hook)
    d.polygon([(sx - 4, y0 + 4), (sx + 9, y0 + 4), (sx + 3, y0 + 18)], fill=metal)
    d.line([sx + 9, y0 + 6, sx + 16, y0 + 12], fill=metal, width=2)  # hook
    d.line([sx + 1, y0 + 16, sx + 1, y0 + 20], fill=metal, width=1)

    # --- shield (round, in front, left hand) ---
    hx, hy = cx - 10, y0 + 34
    d.ellipse([hx - 10, hy - 10, hx + 10, hy + 10], fill=armor)
    noisy(d, hx - 10, hy - 10, 20, 20, armor, jitter=10, seed=idx + 5)
    d.ellipse([hx - 10, hy - 10, hx + 10, hy + 10], outline=metal_lo, width=2)
    d.ellipse([hx - 3, hy - 3, hx + 3, hy + 3], fill=trim)
    # a cross/emboss on the shield
    d.line([hx, hy - 8, hx, hy + 8], fill=metal, width=1)
    d.line([hx - 8, hy, hx + 8, hy], fill=metal, width=1)

    # --- body (uniformed torso, top-down) ---
    d.ellipse([cx - 12, y0 + 24, cx + 12, y0 + 44], fill=armor)
    noisy(d, cx - 12, y0 + 24, 24, 20, armor, jitter=10, seed=idx + 1)
    # belt
    d.line([cx - 12, y0 + 40, cx + 12, y0 + 40], fill=shade(armor, 0.5), width=2)
    d.rectangle([cx - 2, y0 + 38, cx + 2, y0 + 42], fill=metal)
    # shoulder pauldrons
    d.ellipse([cx - 16, y0 + 22, cx - 6, y0 + 32], fill=metal)
    d.ellipse([cx + 6, y0 + 22, cx + 16, y0 + 32], fill=metal)

    # --- head + helm ---
    d.ellipse([cx - 8, y0 + 12, cx + 8, y0 + 28], fill=armor)
    noisy(d, cx - 8, y0 + 12, 16, 16, armor, jitter=10, seed=idx + 2)
    d.ellipse([cx - 8, y0 + 12, cx + 8, y0 + 28], outline=metal_lo, width=2)
    # visor slit
    d.line([cx - 6, y0 + 18, cx + 6, y0 + 18], fill=(20, 20, 24), width=2)
    # helm trim / plume
    d.line([cx, y0 + 10, cx, y0 + 14], fill=trim, width=2)
    d.polygon([(cx - 4, y0 + 8), (cx + 4, y0 + 8), (cx, y0 + 2)], fill=trim)

    # --- weapon in the right hand (sword, raised) ---
    d.line([cx + 8, y0 + 30, cx + 18, y0 + 20], fill=metal, width=2)
    d.line([cx + 16, y0 + 22, cx + 20, y0 + 18], fill=metal_lo, width=2)  # crossguard
    # glint
    d.point((cx + 12, y0 + 26), fill=shade(metal, 1.5))


# Palettes per division (Dark Fantasy, colour-coded by division).
DIVS = [
    {  # Common dottari — street/gate guards, prosperous Spere district. Blue-grey.
        "armor": (96, 116, 140),
        "trim": (176, 190, 210),
    },
    {  # Condottari — canal/river watchers. Deep teal.
        "armor": (52, 104, 108),
        "trim": (140, 200, 196),
    },
    {  # Rundottari — ruin watchers, northern ruins. Rusty red.
        "armor": (132, 60, 52),
        "trim": (200, 130, 110),
    },
    {  # Regidottari — palace guard of government buildings. Deep purple/gold.
        "armor": (96, 64, 128),
        "trim": (210, 190, 120),
    },
]


def main():
    for i, pal in enumerate(DIVS):
        draw_guard(i, i * TILE, 0, pal)
    img.save("guard_tiles.png")
    print("Successfully generated guard_tiles.png (%dx%d): 4 Dottari divisions with transparency."
          % (WIDTH, HEIGHT))


main()
