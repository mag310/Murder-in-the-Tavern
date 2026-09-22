from PIL import Image, ImageDraw
from random import Random, randint, uniform

# --- Pegasus statues + barricade tileset (top-down tokens) ---
# Black background for easy transparency masking. 64x64 tiles.
TILE = 64
WIDTH = TILE * 3   # 3 tiles: pegasus statue, pegasus (broken), barricade
HEIGHT = TILE      # 64 px

img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
BLACK = (0, 0, 0, 0)  # transparent background


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


def clip(v, lo, hi):
    return max(lo, min(hi, v))


def line_pts(d, pts, fill, w=1):
    d.line(pts, fill=fill, width=w)


def draw_pegasus(d, x0, y0, broken=False):
    """Top-down gothic stone pegasus statue; wings are sharp stone/iron swords."""
    L = (x0 + 4, y0 + 4, x0 + TILE - 5, y1 - 5) if False else (x0 + 4, y0 + 4, x0 + TILE - 5, y0 + TILE - 5)
    left, top, right, bot = x0 + 4, y0 + 4, x0 + TILE - 5, y0 + TILE - 5
    rnd = Random(7)

    # stone body of the horse (plan view), weathered limestone
    body = (150, 150, 140)
    body_hi = shade(body, 1.25)
    body_lo = shade(body, 0.6)

    # shadow blob
    d.ellipse([x0 + 12, y0 + 30, x0 + 50, y0 + 58], fill=(0, 0, 0, 90))

    # torso
    d.ellipse([x0 + 18, y0 + 22, x0 + 46, y0 + 46], fill=body)
    noisy(d, x0 + 18, y0 + 22, 28, 24, body, jitter=12, seed=11)
    # haunch
    d.ellipse([x0 + 38, y0 + 26, x0 + 52, y0 + 46], fill=body)
    # neck + head (to the left, rearing)
    d.ellipse([x0 + 8, y0 + 14, x0 + 26, y0 + 30], fill=body)
    d.ellipse([x0 + 4, y0 + 8, x0 + 18, y0 + 22], fill=body)  # head
    noisy(d, x0 + 8, y0 + 14, 18, 16, body, jitter=12, seed=12)
    # mane
    for _ in range(5):
        mx = x0 + randint(10, 24)
        my = y0 + randint(10, 18)
        d.line([mx, my, mx - 2, my - 4], fill=body_lo, width=1)
    # legs (4, short, top-down)
    for lx, ly in [(x0 + 22, y0 + 46), (x0 + 30, y0 + 46), (x0 + 40, y0 + 44), (x0 + 46, y0 + 40)]:
        d.rectangle([lx, ly, lx + 3, ly + 10], fill=body_lo)
    # tail (iron/stone)
    line_pts(d, [x0 + 50, y0 + 30, x0 + 58, y0 + 34, x0 + 56, y0 + 40],
             fill=(90, 92, 98), w=2)

    # --- Wings = sharp stone/iron swords (two blades) ---
    blade = (190, 196, 205)
    steel_lo = shade(blade, 0.6)
    # left blade
    d.polygon([(x0 + 20, y0 + 24), (x0 + 8, y0 - 2), (x0 + 2, y0 + 2),
               (x0 + 16, y0 + 30)], fill=blade)
    d.polygon([(x0 + 20, y0 + 24), (x0 + 12, y0 + 6), (x0 + 16, y0 + 30)],
              fill=steel_lo)
    # right blade
    d.polygon([(x0 + 30, y0 + 26), (x0 + 26, y0 + 0), (x0 + 34, y0 - 4),
               (x0 + 36, y0 + 28)], fill=blade)
    d.polygon([(x0 + 30, y0 + 26), (x0 + 32, y0 + 4), (x0 + 36, y0 + 28)],
              fill=steel_lo)
    # glint
    d.line([x0 + 10, y0 + 4, x0 + 18, y0 + 22], fill=shade(blade, 1.4), width=1)
    d.line([x0 + 28, y0 + 2, x0 + 33, y0 + 24], fill=shade(blade, 1.4), width=1)

    # weathering / cracks on the stone
    for _ in range(6):
        px = x0 + randint(14, 48)
        py = y0 + randint(20, 48)
        d.point((px, py), fill=shade(body, 0.55))
    d.line([x0 + 24, y0 + 34, x0 + 34, y0 + 40, x0 + 40, y0 + 36],
           fill=shade(body, 0.5), width=1)

    # if broken: a chunk of the statue toppled to one side
    if broken:
        # one blade snapped off, lying on the ground
        d.polygon([(x0 + 44, y0 + 48), (x0 + 60, y0 + 56), (x0 + 58, y0 + 60),
                   (x0 + 42, y0 + 52)], fill=blade)
        # crack across the body
        d.line([x0 + 22, y0 + 26, x0 + 30, y0 + 38, x0 + 26, y0 + 44],
               fill=(0, 0, 0, 140), width=2)
        # moss
        for _ in range(4):
            mx = x0 + randint(18, 46)
            my = y0 + randint(30, 46)
            d.point((mx, my), fill=(60, 84, 52, 255))


def draw_barricade(d, x0, y0):
    """Wooden crates, iron chains and stone debris piled as a roadblock."""
    left, top, right, bot = x0 + 4, y0 + 4, x0 + TILE - 5, y0 + TILE - 5
    rnd = Random(7)
    wood = (110, 78, 46)
    wood_lo = shade(wood, 0.6)
    wood_hi = shade(wood, 1.25)
    iron = (120, 124, 132)
    stone = (120, 118, 110)

    # shadow under the pile
    d.ellipse([x0 + 10, y0 + 44, x0 + 54, y0 + 60], fill=(0, 0, 0, 90))

    # --- stone debris (back layer) ---
    for _ in range(5):
        sx = x0 + randint(8, 44)
        sy = y0 + randint(8, 30)
        d.ellipse([sx, sy, sx + randint(8, 14), sy + randint(8, 14)], fill=stone)
        noisy(d, sx, sy, 10, 10, stone, jitter=14, seed=rnd.randint(1, 9999))

    # --- wooden crates (foreground, piled at an angle) ---
    def crate(cx, cy, w, h, ang_sign):
        # a simple box with plank lines, slightly skewed for "pile" look
        x0c, y0c = cx, cy
        x1c, y1c = cx + w, cy + h
        d.rectangle([x0c, y0c, x1c, y1c], fill=wood)
        noisy(d, x0c, y0c, w, h, wood, jitter=12, seed=rnd.randint(1, 9999))
        d.rectangle([x0c, y0c, x1c, y0c + 2], fill=wood_hi)
        d.rectangle([x0c + 2, y0c, x0c + 3, y1c], fill=wood_hi)
        d.rectangle([x0c, y1c - 2, x1c, y1c], fill=wood_lo)
        d.rectangle([x1c - 2, y0c, x1c, y1c], fill=wood_lo)
        # plank seams
        d.line([x0c, (y0c + y1c) // 2, x1c, (y0c + y1c) // 2], fill=wood_lo, width=1)
        d.line([(x0c + x1c) // 2, y0c, (x0c + x1c) // 2, y1c], fill=wood_lo, width=1)

    crate(x0 + 12, y0 + 30, 20, 22, 1)
    crate(x0 + 30, y0 + 28, 18, 24, -1)
    # a crate on top, tilted
    crate(x0 + 22, y0 + 16, 16, 14, 1)

    # --- iron chains draped across the pile ---
    for _ in range(3):
        cx = x0 + randint(14, 44)
        cy = y0 + randint(14, 40)
        d.ellipse([cx, cy, cx + 4, cy + 5], outline=iron, width=1)
        d.ellipse([cx + 3, cy + 3, cx + 7, cy + 8], outline=iron, width=1)
    d.line([x0 + 14, y0 + 20, x0 + 30, y0 + 34, x0 + 46, y0 + 26],
           fill=iron, width=1)

    # a few scattered stone chips in front
    for _ in range(6):
        sx = x0 + randint(10, 50)
        sy = y0 + randint(44, 56)
        d.point((sx, sy), fill=stone)


def main():
    draw_pegasus(draw, 0 * TILE, 0, broken=False)
    draw_pegasus(draw, 1 * TILE, 0, broken=True)
    draw_barricade(draw, 2 * TILE, 0)
    img.save("pegasus_tiles.png")
    print("Successfully generated pegasus_tiles.png (%dx%d): pegasus statue / broken pegasus / barricade."
          % (WIDTH, HEIGHT))


main()
