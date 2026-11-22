"""Make the site icons and the social-card image for openseforim.org.

py -3.13 tools/make_images.py   -> favicon.ico, favicon.svg, apple-touch-icon.png, assets/og.png
Uses Windows fonts (Frank Ruehl for the Hebrew letter, Georgia for the Latin text).
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent.parent
FONTS = Path(r"C:\Windows\Fonts")
ACCENT, BG, FG, MUTED, LINE = "#7a4b12", "#fbfaf7", "#1d1c1a", "#6b665e", "#e3dfd6"
LETTER = "ס"  # samekh, for Seforim


def mark(size):
    """The brand mark: a samekh on a rounded accent square."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=size // 5, fill=ACCENT)
    f = ImageFont.truetype(str(FONTS / "FRANKB.TTF"), int(size * 0.78))
    l, t, r, b = d.textbbox((0, 0), LETTER, font=f)
    d.text(((size - (r - l)) / 2 - l, (size - (b - t)) / 2 - t), LETTER, font=f, fill="#fbfaf7")
    return im


big = mark(512)
big.save(HERE / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
big.resize((180, 180), Image.LANCZOS).convert("RGB").save(HERE / "apple-touch-icon.png")
(HERE / "favicon.svg").write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    f'<rect width="32" height="32" rx="6" fill="{ACCENT}"/>'
    '<text x="16" y="24" font-size="24" text-anchor="middle" fill="#fbfaf7" '
    'font-family="Frank Ruehl CLM, David, Times New Roman, serif" font-weight="700">&#x05E1;</text></svg>\n',
    encoding="utf-8")

# social card 1200x630
W, H = 1200, 630
og = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(og)
d.rectangle([0, H - 14, W, H], fill=ACCENT)
og.paste(mark(170), (90, 120), mark(170))
title = ImageFont.truetype(str(FONTS / "georgiab.ttf"), 92)
sub = ImageFont.truetype(str(FONTS / "georgia.ttf"), 40)
small = ImageFont.truetype(str(FONTS / "georgiai.ttf"), 32)
d.text((300, 130), "Open Seforim", font=title, fill=FG)
d.text((302, 250), "Open readers for Hebrew and Judaica texts", font=sub, fill=MUTED)
d.line([(90, 380), (W - 90, 380)], fill=LINE, width=2)
d.text((90, 410), "Source text, page scans and English translation, side by side.", font=small, fill=FG)
d.text((90, 470), "openseforim.org", font=small, fill=ACCENT)
(HERE / "assets").mkdir(exist_ok=True)
og.save(HERE / "assets" / "og.png", optimize=True)
print("wrote favicon.ico, favicon.svg, apple-touch-icon.png, assets/og.png")
