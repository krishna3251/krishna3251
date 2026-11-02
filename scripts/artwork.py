"""One-time composition of the footer from the supplied artwork."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'assets/one-piece'

def make_footer():
    background = Image.open(ART/'footer-harbor.jpg').convert('RGB')
    background = ImageOps.fit(background, (1200, 400), method=Image.Resampling.LANCZOS).convert('RGBA')
    shade = Image.new('RGBA', background.size)
    draw = ImageDraw.Draw(shade)
    draw.rounded_rectangle((390, 85, 1055, 290), 20, fill=(5, 19, 38, 185), outline=(237, 198, 116, 170), width=2)
    background = Image.alpha_composite(background, shade)
    captain = Image.open(ART/'captain-pointing.png').convert('RGBA')
    captain.thumbnail((340, 390), Image.Resampling.LANCZOS)
    background.alpha_composite(captain, (35, 400-captain.height))
    draw = ImageDraw.Draw(background)
    draw.text((430, 117), 'JOIN MY CREW', font=ImageFont.truetype('DejaVuSans-Bold.ttf', 52), fill='#fff1c8', stroke_width=1, stroke_fill='#40301c')
    draw.line((433, 193, 910, 193), fill='#e9c27c', width=2)
    draw.text((434, 215), 'BOTS  /  WEB  /  AI  /  DESIGN', font=ImageFont.truetype('DejaVuSansMono.ttf', 20), fill='#e9e4d4')
    background.convert('RGB').save(ART/'crew-footer.jpg', quality=90, subsampling=0, optimize=True)

if __name__ == '__main__':
    make_footer()
