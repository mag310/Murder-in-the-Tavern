from PIL import Image, ImageDraw

# Spritesheet specifications
TILE_SIZE = 64
COLS = 14
WIDTH = TILE_SIZE * COLS  # 896 px
HEIGHT = TILE_SIZE        # 64 px

# Create transparency canvas
img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Palettes (Dark Fantasy Style)
palette = {
    0:  ((46, 75, 43),   (34, 58, 32)),     # Grass
    1:  ((101, 77, 54),  (74, 53, 34)),     # Dirt
    2:  ((54, 40, 31),   (36, 26, 20)),     # Mud
    3:  ((35, 59, 74),   (22, 38, 49)),     # Murky Water
    4:  ((80, 85, 90),   (55, 58, 62)),     # Paver Road
    5:  ((120, 110, 95), (90, 82, 70)),     # Gravel Path
    6:  ((70, 65, 60),   (45, 42, 40)),     # Cliff Rock
    7:  ((115, 85, 55),  (60, 40, 20)),     # Fence H
    8:  ((115, 85, 55),  (60, 40, 20)),     # Fence V
    9:  ((90, 95, 100),  (40, 45, 50)),     # Main Gate H
    10: ((50, 45, 60),   (30, 25, 40)),     # Tavern Roof
    11: ((110, 95, 70),  (70, 60, 40)),     # Stable Roof
    12: ((70, 75, 75),   (35, 40, 40)),     # Grave Fence H
    13: ((70, 75, 75),   (35, 40, 40)),     # Grave Fence V
}

for i in range(COLS):
    x0, y0 = i * TILE_SIZE, 0
    x1, y1 = x0 + TILE_SIZE, HEIGHT

    bg_color, fg_color = palette[i]

    # Texturing Base Blocks
    if i in range(0, 7):
        draw.rectangle([x0, y0, x1, y1], fill=bg_color)
        # Noise / Texturing lines inside tiles
        for step in range(4, 64, 8):
            draw.line([x0, step, x1, step], fill=fg_color, width=1)

    # Structural Tiles (Fences / Gates) with transparent backing
    elif i == 7: # Fence H
        draw.rectangle([x0, y0 + 20, x1, y0 + 28], fill=bg_color)
        draw.rectangle([x0, y0 + 40, x1, y0 + 48], fill=bg_color)
        for p in range(x0 + 8, x1, 16):
            draw.rectangle([p, y0 + 10, p + 6, y1 - 10], fill=fg_color)
    elif i == 8: # Fence V
        draw.rectangle([x0 + 24, y0, x0 + 40, y1], fill=bg_color)
        draw.line([x0 + 24, y0 + 16, x0 + 40, y0 + 24], fill=fg_color, width=3)
        draw.line([x0 + 24, y0 + 40, x0 + 40, y0 + 48], fill=fg_color, width=3)
    elif i == 9: # Gate H
        draw.rectangle([x0, y0 + 12, x1, y1 - 12], fill=bg_color, outline=fg_color, width=3)
        draw.line([x0, y0 + 12, x1, y1 - 12], fill=fg_color, width=2)
        draw.line([x0, y1 - 12, x1, y0 + 12], fill=fg_color, width=2)
    elif i == 12: # Grave Fence H
        draw.line([x0, y0 + 24, x1, y0 + 24], fill=bg_color, width=4)
        draw.line([x0, y0 + 48, x1, y0 + 48], fill=bg_color, width=4)
        for p in range(x0 + 4, x1, 12):
            draw.line([p, y0 + 10, p, y0 + 54], fill=fg_color, width=2)
    elif i == 13: # Grave Fence V
        for offset in range(10, 64, 16):
            draw.rectangle([x0 + offset, y0, x0 + offset + 6, y1], fill=bg_color)
            draw.polygon([x0 + offset - 2, y0 + 8, x0 + offset + 3, y0, x0 + offset + 8, y0 + 8], fill=fg_color)

# Save output natively
img.save("yard_tiles.png")
print("Successfully generated yard_tiles.png (896x64) with perfect transparency.")