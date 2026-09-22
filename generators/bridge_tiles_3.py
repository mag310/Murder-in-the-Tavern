#!/usr/bin/env python3
"""
Генератор тайлсета для карты Bladewing Bridge.
Создаёт bridge_tiles.png (256x32 px, 8 тайлов по 32x32).
Требуется: pip install Pillow
"""

import random
from PIL import Image, ImageDraw

TILE = 32
TILES = 8
random.seed(42)  # фиксированный seed — одинаковый результат при каждом запуске


def new_tile():
    return Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))


# ---------------------------------------------------------------- 1. ВОДА
def tile_water():
    img = new_tile()
    d = ImageDraw.Draw(img)
    # базовый синий градиент
    for y in range(TILE):
        shade = 40 + int(30 * (y / TILE))
        d.line([(0, y), (TILE, y)], fill=(20, shade, 120, 255))
    # волны
    for _ in range(6):
        x = random.randint(0, TILE - 8)
        y = random.randint(0, TILE - 1)
        d.line([(x, y), (x + 6, y)], fill=(90, 160, 220, 180))
    return img


# ---------------------------------------------------------------- 2. МОСТ
def tile_bridge():
    img = new_tile()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=(120, 118, 112, 255))
    # кладка камней
    for row in range(0, TILE, 8):
        offset = 0 if (row // 8) % 2 == 0 else 8
        for col in range(-8, TILE, 16):
            x0 = col + offset
            d.rectangle([x0, row, x0 + 14, row + 6],
                        outline=(85, 83, 78, 255), fill=(132, 130, 124, 255))
    # трещины
    for _ in range(3):
        x, y = random.randint(2, 28), random.randint(2, 28)
        d.line([(x, y), (x + random.randint(-5, 5), y + random.randint(2, 5))],
               fill=(70, 68, 64, 255))
    return img


# ---------------------------------------------------------------- 3. ПАРАПЕТ
def tile_parapet():
    img = new_tile()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=(75, 73, 70, 255))
    # верхний светлый край
    d.rectangle([0, 0, TILE - 1, 4], fill=(105, 102, 98, 255))
    # зубцы сверху
    for x in range(0, TILE, 8):
        d.rectangle([x, 0, x + 4, 3], fill=(50, 48, 46, 255))
    # тени
    d.rectangle([0, TILE - 3, TILE - 1, TILE - 1], fill=(45, 43, 41, 255))
    return img


# ---------------------------------------------------------------- 4. ЗЕМЛЯ
def tile_ground():
    img = new_tile()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=(128, 108, 82, 255))
    # пятна
    for _ in range(20):
        x, y = random.randint(0, TILE - 2), random.randint(0, TILE - 2)
        shade = random.randint(-15, 15)
        c = (128 + shade, 108 + shade, 82 + shade, 255)
        d.point((x, y), fill=c)
    # камешки
    for _ in range(5):
        x, y = random.randint(2, 28), random.randint(2, 28)
        d.ellipse([x, y, x + 2, y + 1], fill=(100, 90, 75, 255))
    return img


# ---------------------------------------------------------------- 5. СТАТУЯ ПЕГАСА
def tile_statue():
    img = new_tile()
    d = ImageDraw.Draw(img)
    # фон — парапет
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=(75, 73, 70, 255))
    # пьедестал
    d.rectangle([8, 24, 23, 31], fill=(95, 92, 88, 255),
                outline=(55, 53, 50, 255))
    # тело коня
    d.ellipse([10, 12, 22, 24], fill=(150, 148, 142, 255),
              outline=(70, 68, 64, 255))
    # шея и голова
    d.polygon([(18, 12), (23, 4), (26, 6), (21, 14)],
              fill=(150, 148, 142, 255), outline=(70, 68, 64, 255))
    # крыло-меч (торчит вверх)
    d.polygon([(11, 14), (7, 2), (9, 1), (13, 13)],
              fill=(180, 178, 172, 255), outline=(70, 68, 64, 255))
    d.polygon([(13, 13), (17, 3), (19, 4), (15, 14)],
              fill=(170, 168, 162, 255), outline=(70, 68, 64, 255))
    # ноги
    d.line([(12, 22), (11, 27)], fill=(90, 88, 84, 255), width=2)
    d.line([(20, 22), (21, 27)], fill=(90, 88, 84, 255), width=2)
    return img


# ---------------------------------------------------------------- 6. ФОНАРЬ
def tile_lantern():
    img = new_tile()
    d = ImageDraw.Draw(img)
    # фон — парапет
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=(75, 73, 70, 255))
    # столб
    d.rectangle([14, 12, 17, 31], fill=(60, 55, 50, 255))
    # фонарный корпус
    d.rectangle([10, 4, 21, 14], fill=(45, 42, 38, 255),
                outline=(25, 22, 20, 255))
    # стекло и огонь
    d.rectangle([12, 6, 19, 12], fill=(255, 200, 80, 255))
    d.ellipse([14, 7, 17, 11], fill=(255, 240, 160, 255))
    # блик
    d.point((13, 7), fill=(255, 255, 220, 255))
    # крышка
    d.polygon([(9, 4), (22, 4), (19, 1), (12, 1)],
              fill=(40, 38, 35, 255))
    return img


# ---------------------------------------------------------------- 7. БАРРИКАДА
def tile_barricade():
    img = new_tile()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=(120, 118, 112, 255))
    # две диагональные балки
    d.line([(0, 26), (31, 6)], fill=(90, 60, 35, 255), width=6)
    d.line([(0, 6), (31, 26)], fill=(80, 52, 30, 255), width=6)
    # гвозди
    for x, y in [(4, 22), (26, 22), (4, 10), (26, 10)]:
        d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(50, 48, 45, 255))
    # заострённые колья поверх
    for x in [6, 16, 26]:
        d.polygon([(x - 2, 0), (x + 2, 0), (x, 5)], fill=(60, 40, 22, 255))
    return img


# ---------------------------------------------------------------- 8. ОБЛОМКИ
def tile_debris():
    img = new_tile()
    d = ImageDraw.Draw(img)
    # фон — мост
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=(120, 118, 112, 255))
    # крупный обломок
    d.polygon([(4, 20), (12, 14), (18, 20), (14, 26), (6, 26)],
              fill=(110, 108, 102, 255), outline=(70, 68, 64, 255))
    # средние камни
    d.ellipse([18, 8, 24, 14], fill=(100, 98, 92, 255),
              outline=(65, 63, 60, 255))
    d.ellipse([24, 20, 30, 26], fill=(105, 102, 96, 255),
              outline=(65, 63, 60, 255))
    # мелкая крошка
    for _ in range(8):
        x, y = random.randint(1, 30), random.randint(1, 30)
        d.point((x, y), fill=(80, 78, 74, 255))
    # трещина на мосту
    d.line([(0, 12), (8, 16), (14, 12)], fill=(70, 68, 64, 255))
    return img


# ---------------------------------------------------------------- СБОРКА
def main():
    builders = [
        tile_water,
        tile_bridge,
        tile_parapet,
        tile_ground,
        tile_statue,
        tile_lantern,
        tile_barricade,
        tile_debris,
    ]

    sheet = Image.new("RGBA", (TILE * TILES, TILE), (0, 0, 0, 0))
    for i, build in enumerate(builders):
        sheet.paste(build(), (i * TILE, 0))

    sheet.save("bridge_tiles_3.png")
    print("Готово: bridge_tiles.png (256x32, 8 тайлов)")


if __name__ == "__main__":
    main()