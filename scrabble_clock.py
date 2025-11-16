#!/usr/bin/env python3
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw, ImageFont
import datetime
import time

# ----------------------
# GRID CONFIGURATION
# ----------------------
GRID = [
    "ITLISASTIME",   # ROW 0 — IGNORED
    "ACQUARTERDC",
    "TWENTYFIVEX",
    "HALFBTENYTO",
    "PASTERUNINE",
    "ONESIXTHREE",
    "FOURFIVETWO",
    "EIGHTELEVEN",
    "SEVENTWELVE",
    "OCLOCKXXXXX"
]

ROWS = len(GRID)
COLS = len(GRID[0])

CELL_W = 6
CELL_H = 3

IMG_W = 64
IMG_H = 32

OFFSET_X = (IMG_W - COLS * CELL_W) // 2 + 2 # shifted the whole grid 2 pixels to the right so the words are within frmae

# ----------------------
# WORD MAPPINGS
# ----------------------
WORDS = {
    "QUARTER":   [(1, 2, 1, 8)],
    "TWENTY":    [(2, 0, 2, 5)],
    "FIVE":      [(2, 6, 2, 9)],
    "HALF":      [(3, 0, 3, 3)],
    "TEN":       [(3, 5, 3, 7)],
    "TO":        [(3, 9, 3, 10)],
    "PAST":      [(4, 0, 4, 3)],
    "ONE":       [(5, 0, 5, 2)],
    "TWO":       [(6, 7, 6, 9)],
    "THREE":     [(5, 4, 5, 8)],
    "FOUR":      [(6, 0, 6, 3)],
    "FIVE_H":    [(6, 4, 6, 7)],
    "SIX":       [(5, 3, 5, 5)],
    "SEVEN":     [(8, 0, 8, 4)],
    "EIGHT":     [(7, 0, 7, 4)],
    "NINE":      [(4, 6, 4, 9)],
    "TEN_H":     [(3, 5, 3, 7)],
    "ELEVEN":    [(7, 5, 7, 10)],
    "TWELVE":    [(8, 5, 8, 10)],
    "OCLOCK":    [(9, 0, 9, 5)]
}

# ----------------------
# BRAILLE (2×3)
# ----------------------
BRAILLE = {
    "A": [(0,0)],
    "P": [(0,0), (1,0), (2,0), (0,1)]
}

# ----------------------
# HELPERS
# ----------------------
def expand(word):
    coords = []
    for w in WORDS[word]:
        if len(w) == 2:
            coords.append(w)
        elif len(w) == 3:
            r, s, e = w
            coords.extend([(r, c) for c in range(s, e + 1)])
        elif len(w) == 4:
            r1, c1, r2, c2 = w
            for r in range(r1, r2 + 1):
                for c in range(c1, c2 + 1):
                    coords.append((r, c))
    return coords

def num_word(n, hour=False):
    mapping = {
        1: "ONE", 2: "TWO", 3: "THREE",
        4: "FOUR", 5: "FIVE_H" if hour else "FIVE",
        6: "SIX", 7: "SEVEN", 8: "EIGHT",
        9: "NINE", 10: "TEN_H" if hour else "TEN",
        11: "ELEVEN", 12: "TWELVE"
    }
    return mapping[n]

def time_words():
    now = datetime.datetime.now()
    h = now.hour % 12 or 12
    m = now.minute
    minute = (m // 5) * 5
    next_hour = (h % 12) + 1
    words = []

    if minute == 0:
        words += [num_word(h, hour=True), "OCLOCK"]
    elif minute == 5:
        words += ["FIVE", "PAST", num_word(h)]
    elif minute == 10:
        words += ["TEN", "PAST", num_word(h)]
    elif minute == 15:
        words += ["QUARTER", "PAST", num_word(h)]
    elif minute == 20:
        words += ["TWENTY", "PAST", num_word(h)]
    elif minute == 25:
        words += ["TWENTY", "FIVE", "PAST", num_word(h)]
    elif minute == 30:
        words += ["HALF", "PAST", num_word(h)]
    elif minute == 35:
        hour_word = num_word(next_hour, hour=next_hour in [5,10])
        words += ["TWENTY", "FIVE", "TO", hour_word]
    elif minute == 40:
        hour_word = num_word(next_hour, hour=next_hour in [5,10])
        words += ["TWENTY", "TO", hour_word]
    elif minute == 45:
        hour_word = num_word(next_hour, hour=next_hour in [5,10])
        words += ["QUARTER", "TO", hour_word]
    elif minute == 50:
        hour_word = num_word(next_hour, hour=next_hour in [5,10])
        words += ["TEN", "TO", hour_word]
    elif minute == 55:
        hour_word = num_word(next_hour, hour=next_hour in [5,10])
        words += ["FIVE", "TO", hour_word]

    return words

# ----------------------
# MATRIX SETUP
# ----------------------
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.gpio_slowdown = 4
matrix = RGBMatrix(options=options)

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 5)

# ----------------------
# MAIN LOOP
# ----------------------
while True:
    now = datetime.datetime.now()
    time.sleep(60 - now.second)

    now = datetime.datetime.now()
    words = time_words()
    img = Image.new("RGB", (IMG_W, IMG_H), "black")
    draw = ImageDraw.Draw(img)

    # --- DRAW ALL LETTERS (skip row 0, shift up)
    for r in range(1, ROWS):
        for c in range(COLS):
            x = OFFSET_X + c * CELL_W
            y = (r - 1) * CELL_H
            draw.text((x, y), GRID[r][c], fill=(50,50,50), font=font)

    # --- HIGHLIGHTS
    for w in words:
        for r, c in expand(w):
            if r == 0:
                continue
            x = OFFSET_X + c * CELL_W
            y = (r - 1) * CELL_H
            draw.text((x, y), GRID[r][c], fill=(255,255,255), font=font)

    # --- AM/PM BRAILLE (always red)
    letter = "A" if now.hour < 12 else "P"
    block_x = IMG_W - 3
    block_y = 0
    for dy, dx in BRAILLE[letter]:
        draw.point((block_x + dx, block_y + dy), fill=(255,0,0))

    # --- CROP SO BOTTOM 2 LED ROWS ARE UNUSED
    safe = img.crop((0, 0, IMG_W, 30))
    matrix.SetImage(safe, 0, 0)
