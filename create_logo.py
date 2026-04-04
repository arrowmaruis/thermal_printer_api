#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Genere le logo / icone de Thermal Printer API
  - logo.png  : 512x512 (pour l'installateur GUI)
  - icon.ico  : multi-taille (16/32/48/64/128/256) pour le .exe
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUT_DIR = Path(__file__).parent
BG      = (26,  26,  46)   # #1a1a2e  fond sombre
ACCENT  = (108, 92, 231)   # #6c5ce7  violet
WHITE   = (255, 255, 255)
LIGHT   = (200, 200, 230)
PAPER   = (245, 245, 240)


def draw_logo(size=512):
    img  = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    s    = size

    # ── Fond rond ────────────────────────────────────────────────────────────
    r = s // 8
    draw.rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=BG)

    # ── Corps de l'imprimante ─────────────────────────────────────────────────
    px0 = int(s * 0.15)
    px1 = int(s * 0.85)
    py0 = int(s * 0.35)
    py1 = int(s * 0.68)
    pr  = int(s * 0.06)
    draw.rounded_rectangle([px0, py0, px1, py1], radius=pr, fill=ACCENT)

    # Reflet haut du boitier
    draw.rounded_rectangle(
        [px0 + int(s*0.02), py0 + int(s*0.02),
         px1 - int(s*0.02), py0 + int(s*0.08)],
        radius=pr // 2,
        fill=(140, 120, 255, 80)
    )

    # ── Fente papier (haut) ───────────────────────────────────────────────────
    sx0 = int(s * 0.30)
    sx1 = int(s * 0.70)
    sy0 = int(s * 0.33)
    sy1 = int(s * 0.37)
    draw.rounded_rectangle([sx0, sy0, sx1, sy1], radius=3, fill=BG)

    # ── Recu qui sort ────────────────────────────────────────────────────────
    rw0 = int(s * 0.33)
    rw1 = int(s * 0.67)
    rh0 = int(s * 0.10)
    rh1 = int(s * 0.36)
    draw.rounded_rectangle([rw0, rh0, rw1, rh1], radius=4, fill=PAPER)

    # Lignes imprimées sur le reçu
    lx0 = rw0 + int(s * 0.03)
    lx1 = rw1 - int(s * 0.03)
    line_color = (160, 160, 155)
    for i, frac in enumerate([0.16, 0.21, 0.26]):
        ly = int(s * frac)
        w  = int(s * 0.015) if i % 2 == 0 else int(s * 0.012)
        draw.rectangle([lx0, ly, lx1, ly + w], fill=line_color)

    # Ligne titre en haut du reçu (plus sombre)
    draw.rectangle([lx0, int(s * 0.12), lx1, int(s * 0.14)], fill=(80, 80, 80))

    # ── Bouton LED sur l'imprimante ───────────────────────────────────────────
    cx = int(s * 0.72)
    cy = int(s * 0.515)
    cr = int(s * 0.035)
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(0, 230, 120))
    # reflet
    draw.ellipse([cx - cr//2, cy - cr//2, cx, cy], fill=(150, 255, 180, 180))

    # ── Texte "TPA" sous l'imprimante ─────────────────────────────────────────
    label_y = int(s * 0.73)
    font_size = max(20, s // 9)
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    text = "ThermalPrint"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((s - tw) // 2, label_y), text, font=font, fill=WHITE)

    sub_font_size = max(10, s // 20)
    try:
        sub_font = ImageFont.truetype("arial.ttf", sub_font_size)
    except Exception:
        try:
            sub_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", sub_font_size)
        except Exception:
            sub_font = ImageFont.load_default()

    sub = "API"
    sbbox = draw.textbbox((0, 0), sub, font=sub_font)
    sw = sbbox[2] - sbbox[0]
    draw.text(((s - sw) // 2, label_y + font_size + int(s * 0.01)), sub,
              font=sub_font, fill=(180, 170, 255))

    return img


def main():
    print("Generation du logo...")

    # PNG 512x512
    logo = draw_logo(512)
    logo_path = OUT_DIR / "logo.png"
    logo.convert('RGB').save(logo_path, 'PNG')
    print(f"  logo.png     : {logo_path}")

    # ICO multi-taille
    sizes = [16, 32, 48, 64, 128, 256]
    frames = [draw_logo(sz).convert('RGBA') for sz in sizes]
    ico_path = OUT_DIR / "icon.ico"
    frames[0].save(
        ico_path, format='ICO',
        sizes=[(sz, sz) for sz in sizes],
        append_images=frames[1:]
    )
    print(f"  icon.ico     : {ico_path}")
    print("Done.")


if __name__ == '__main__':
    main()
