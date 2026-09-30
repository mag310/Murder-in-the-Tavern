#!/usr/bin/env python3
import numpy as np
from PIL import Image, ImageDraw

rng = np.random.default_rng(42)
OUT = 64
COLS, ROWS = 4, 3
canvas = Image.new("RGBA", (COLS * OUT, ROWS * OUT))


def _gaussian(arr, sigma):
    k = int(6 * sigma + 1)
    x = np.arange(k) - k // 2
    g = np.exp(-x * x / (2 * sigma * sigma))
    g /= g.sum()
    out = arr.copy()
    for i in range(k):
        for j in range(k):
            out = out + arr * g[i] * g[j]
    return out


def perlin(size, scale, seed):
    r = np.random.default_rng(seed)
    small = r.random((max(8, size // 4), max(8, size // 4)))
    big = np.repeat(np.repeat(small, size // small.shape[0], axis=0),
                    size // small.shape[1], axis=1)[:size, :size]
    return _gaussian(big, scale)


def base_noise(size, scale, seed):
    p = perlin(size, scale, seed)
    p = (p - p.mean()) / max(p.std(), 1e-6)
    return p


def add_dirt(img_arr, amount=12, seed=1):
    r = np.random.default_rng(seed)
    n, m, _ = img_arr.shape
    for _ in range(amount):
        x, y = int(r.uniform(0, n)), int(r.uniform(0, m))
        rad = int(r.uniform(1, 6))
        for dy in range(-rad, rad + 1):
            for dx in range(-rad, rad + 1):
                if dx * dx + dy * dy > rad * rad:
                    continue
                yy = np.clip(y + dy, 0, n - 1)
                xx = np.clip(x + dx, 0, m - 1)
                img_arr[yy, xx, :3] = (img_arr[yy, xx, :3] * 0.6).astype(np.uint8)


def add_stain(img_arr, color, alpha=0.3, size=20, seed=2):
    r = np.random.default_rng(seed)
    x, y = int(r.uniform(0, 64)), int(r.uniform(0, 64))
    rad = size
    color = np.array(color, dtype=np.float64)
    for dy in range(-rad, rad + 1):
        for dx in range(-rad, rad + 1):
            if dx * dx + dy * dy > rad * rad:
                continue
            yy = np.clip(y + dy, 0, 63)
            xx = np.clip(x + dx, 0, 63)
            for c in range(3):
                val = (1 - alpha) * float(img_arr[yy, xx, c]) + alpha * color[c]
                img_arr[yy, xx, c] = int(val)


def tile_base(base_color, seed, scale=8):
    n = base_noise(64, scale, seed)
    arr = np.zeros((64, 64, 4), dtype=np.float64)
    for c in range(3):
        arr[:, :, c] = (base_color[c] + n * 15).clip(0, 255)
    arr[:, :, 3] = 255
    add_dirt(arr, amount=10, seed=seed + 7)
    return arr.astype(np.uint8)


def draw_cracks(draw, arr, color, width=1, count=6, seed=11):
    r = np.random.default_rng(seed)
    for _ in range(count):
        x = int(r.uniform(0, 64)); y = int(r.uniform(0, 64))
        x2 = int(r.uniform(x - 10, x + 10)); y2 = int(r.uniform(y - 10, y + 10))
        draw.line([(x, y), (x2, y2)], fill=color, width=width)


def draw_scratches(arr, color, count=40, seed=5):
    r = np.random.default_rng(seed)
    for _ in range(count):
        x = int(r.uniform(0, 64)); y = int(r.uniform(0, 64))
        l = int(r.uniform(2, 8))
        for i in range(l):
            yy = np.clip(y + i, 0, 63)
            arr[yy, x, :3] = color


def draw_moss(arr, seed=3):
    r = np.random.default_rng(seed)
    for _ in range(5):
        x = int(r.uniform(0, 64)); y = int(r.uniform(0, 64))
        rad = int(r.uniform(3, 7))
        yy, xx = np.ogrid[-rad:rad + 1, -rad:rad + 1]
        mask = xx * xx + yy * yy <= rad * rad
        yy = np.clip(y + yy, 0, 63)
        xx = np.clip(x + xx, 0, 63)
        a = mask * 0.4
        for c in range(3):
            arr[yy, xx, c] = (1 - a) * arr[yy, xx, c] + a * [74, 93, 58][c]


def draw_wood(arr, color, seed=9, x=0, y=0, w=64, h=64):
    r = np.random.default_rng(seed)
    for i in range(0, w, 3):
        for j in range(0, h, 2):
            px = np.clip(x + i, 0, 63)
            py = np.clip(y + j, 0, 63)
            grain = 1 - 0.3 * abs(np.sin((i + j) * 0.3))
            arr[py, px, :3] = np.array(color) * grain
            if r.random() < 0.03:
                arr[py, px, :3] = np.array([30, 20, 10])


def tile_cobblestone():
    arr = tile_base([107, 107, 99], seed=1, scale=6)
    img = Image.fromarray(arr, "RGBA")
    draw = ImageDraw.Draw(img)
    for i in range(64):
        draw.line([(i, 0), (i, 64)], fill=(90, 90, 82), width=1)
        draw.line([(0, i), (64, i)], fill=(90, 90, 82), width=1)
    draw_cracks(draw, arr, (58, 58, 53), width=1, count=8, seed=11)
    arr2 = np.array(img)
    add_stain(arr2, [74, 93, 58], alpha=0.15, size=4, seed=13)
    for _ in range(30):
        x = int(rng.uniform(0, 64)); y = int(rng.uniform(0, 64))
        arr2[y, x, :3] = [80, 80, 72]
    return np.array(Image.fromarray(arr2, "RGBA"))


def tile_wall():
    arr = tile_base([74, 74, 69], seed=2, scale=4)
    img = Image.fromarray(arr, "RGBA")
    draw = ImageDraw.Draw(img)
    for y in range(0, 64, 16):
        draw.line([(0, y), (64, y)], fill=(50, 50, 45), width=1)
    for x in range(0, 64, 32):
        draw.line([(x, 0), (x, 64)], fill=(50, 50, 45), width=1)
    arr2 = np.array(img)
    for y in range(48, 64):
        arr2[y, :, :3] = arr2[y, :, :3] * 0.6 + np.array([46, 46, 42]) * 0.4
    add_stain(arr2, [46, 46, 42], alpha=0.4, size=10, seed=17)
    return arr2


def tile_wall_window():
    arr = tile_base([74, 74, 69], seed=3, scale=5)
    img = Image.fromarray(arr, "RGBA")
    draw = ImageDraw.Draw(img)
    wx, wy, ww, wh = 20, 16, 24, 32
    draw.rectangle([wx, wy, wx + ww, wy + wh], fill=(20, 20, 18))
    for i in range(0, ww, 3):
        draw.line([(wx + i, wy), (wx + i + ww, wy + wh)], fill=(58, 42, 26), width=2)
        draw.line([(wx + ww, wy + i), (wx, wy + i + wh)], fill=(58, 42, 26), width=2)
    arr2 = np.array(img)
    for _ in range(20):
        x = wx + int(rng.uniform(0, ww)); y = wy + int(rng.uniform(0, wh))
        arr2[y, x, :3] = [120, 120, 120]
    add_stain(arr2, [46, 46, 42], alpha=0.3, size=8, seed=19)
    return arr2


def tile_wall_door():
    arr = tile_base([74, 74, 69], seed=4, scale=5)
    img = Image.fromarray(arr, "RGBA")
    draw = ImageDraw.Draw(img)
    dx, dy = 18, 10
    draw.rectangle([dx, dy, dx + 28, dy + 50], fill=(25, 20, 15))
    for i in range(6):
        y = dy + 2 + i * 8
        draw.line([(dx + 2, y), (dx + 26, y + 4)], fill=(60, 45, 30), width=3)
        draw.line([(dx + 2, y + 5), (dx + 26, y - 1)], fill=(60, 45, 30), width=3)
    arr2 = np.array(img)
    add_stain(arr2, [30, 25, 18], alpha=0.5, size=12, seed=21)
    add_dirt(arr2, amount=15, seed=23)
    return arr2


def tile_barricade():
    arr = np.zeros((64, 64, 4), dtype=np.uint8)
    arr[:, :, :3] = [30, 25, 18]
    arr[:, :, 3] = 255
    img = Image.fromarray(arr, "RGBA")
    draw = ImageDraw.Draw(img)
    draw_wood(img, [74, 53, 32], seed=31, x=0, y=8, w=64, h=12)
    draw_wood(img, [74, 53, 32], seed=32, x=0, y=40, w=64, h=12)
    draw.ellipse([10, 22, 30, 42], fill=(60, 45, 28))
    draw.ellipse([34, 20, 54, 40], fill=(60, 45, 28))
    draw.rectangle([15, 18, 25, 28], outline=(80, 65, 45), width=1)
    arr2 = np.array(img)
    for _ in range(15):
        x = int(rng.uniform(0, 64)); y = int(rng.uniform(0, 64))
        arr2[y, x, :3] = [100, 100, 100]
    return arr2


def draw_wood(img, color, seed, x, y, w, h):
    r = np.random.default_rng(seed)
    arr = np.array(img)
    for i in range(0, w, 3):
        for j in range(0, h, 2):
            px = np.clip(x + i, 0, 63)
            py = np.clip(y + j, 0, 63)
            grain = 1 - 0.3 * abs(np.sin((i + j) * 0.3))
            arr[py, px, :3] = np.array(color) * grain
            if r.random() < 0.03:
                arr[py, px, :3] = [30, 20, 10]
    Image.fromarray(arr, "RGBA")


def tile_debris():
    arr = tile_base([90, 90, 82], seed=5, scale=7)
    img = Image.fromarray(arr, "RGBA")
    arr2 = np.array(img)
    for _ in range(20):
        x = int(rng.uniform(0, 64)); y = int(rng.uniform(0, 64))
        w = int(rng.uniform(3, 8))
        arr2[y:y + 2, x:x + w, :3] = [60, 50, 40]
        arr2[y:y + 2, x:x + w, 3] = 120
    add_dirt(arr2, amount=20, seed=27)
    return arr2


def tile_puddle():
    arr = np.zeros((64, 64, 4), dtype=np.uint8)
    arr[:, :, :3] = [58, 74, 58]
    arr[:, :, 3] = 255
    img = Image.fromarray(arr, "RGBA")
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 20, 56, 50], fill=(70, 85, 70))
    draw.ellipse([15, 25, 49, 45], outline=(90, 106, 90), width=1)
    for _ in range(10):
        x = int(rng.uniform(8, 56)); y = int(rng.uniform(20, 50))
        draw.ellipse([x, y, x + 3, y + 1], fill=(90, 106, 90))
    arr2 = np.array(img)
    add_stain(arr2, [40, 50, 40], alpha=0.3, size=6, seed=33)
    return arr2


def tile_shadow():
    arr = np.zeros((64, 64, 4), dtype=np.uint8)
    arr[:, :, :3] = [30, 30, 30]
    arr[:, :, 3] = 140
    img = Image.fromarray(arr, "RGBA")
    draw = ImageDraw.Draw(img)
    draw.ellipse([6, 6, 58, 58], fill=(40, 40, 40, 120))
    arr2 = np.array(img)
    for _ in range(30):
        x = int(rng.uniform(0, 64)); y = int(rng.uniform(0, 64))
        if x * x + y * y < 900:
            arr2[y, x, 3] = 100
    return arr2


def tile_rubble():
    arr = tile_base([95, 85, 70], seed=6, scale=5)
    img = Image.fromarray(arr, "RGBA")
    draw = ImageDraw.Draw(img)
    for _ in range(12):
        x = int(rng.uniform(5, 55)); y = int(rng.uniform(5, 55))
        w = int(rng.uniform(8, 18)); h = int(rng.uniform(6, 14))
        draw.rectangle([x, y, x + w, y + h], fill=(70, 60, 50), outline=(50, 45, 40))
    arr2 = np.array(img)
    add_dirt(arr2, amount=15, seed=37)
    return arr2


def tile_wall_vine():
    arr = tile_base([74, 74, 69], seed=7, scale=5)
    img = Image.fromarray(arr, "RGBA")
    draw = ImageDraw.Draw(img)
    for _ in range(8):
        x = int(rng.uniform(0, 64)); y = int(rng.uniform(0, 64))
        draw.ellipse([x, y, x + 8, y + 6], fill=(46, 74, 42))
    for _ in range(5):
        x = int(rng.uniform(0, 64)); y = int(rng.uniform(0, 64))
        draw.line([(x, y), (x + int(rng.uniform(3, 10)), y + int(rng.uniform(3, 10)))], fill=(35, 55, 30), width=1)
    arr2 = np.array(img)
    add_stain(arr2, [46, 74, 42], alpha=0.3, size=5, seed=39)
    return arr2


def tile_cart():
    arr = np.zeros((64, 64, 4), dtype=np.uint8)
    arr[:, :, :3] = [35, 28, 20]
    arr[:, :, 3] = 255
    img = Image.fromarray(arr, "RGBA")
    draw = ImageDraw.Draw(img)
    draw.ellipse([10, 10, 40, 40], outline=(60, 45, 30), width=3)
    draw.ellipse([15, 15, 35, 35], fill=(25, 20, 15))
    draw.line([(5, 25), (59, 25)], fill=(70, 55, 40), width=4)
    draw.line([(5, 25), (20, 45)], fill=(70, 55, 40), width=3)
    draw.line([(59, 25), (45, 45)], fill=(70, 55, 40), width=3)
    arr2 = np.array(img)
    add_dirt(arr2, amount=10, seed=41)
    return arr2


def tile_dirt():
    arr = tile_base([58, 46, 26], seed=8, scale=6)
    img = Image.fromarray(arr, "RGBA")
    arr2 = np.array(img)
    add_stain(arr2, [40, 30, 18], alpha=0.4, size=10, seed=43)
    for _ in range(15):
        x = int(rng.uniform(0, 64)); y = int(rng.uniform(0, 64))
        arr2[y, x, :3] = [80, 75, 70]
    return arr2


tile_fns = [
    tile_cobblestone, tile_wall, tile_wall_window, tile_wall_door,
    tile_barricade, tile_debris, tile_puddle, tile_shadow,
    tile_rubble, tile_wall_vine, tile_cart, tile_dirt,
]

for idx, fn in enumerate(tile_fns):
    col, row = idx % COLS, idx // COLS
    tile = Image.fromarray(fn(), "RGBA")
    tile = tile.crop((0, 0, OUT, OUT))
    canvas.paste(tile, (col * OUT, row * OUT))

canvas.save("maps/rego_cader_tileset.png")
print("Generated maps/rego_cader_tileset.png", canvas.size)
