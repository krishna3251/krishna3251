"""Compose static profile panels once from the supplied artwork and transparent PNGs."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'assets/one-piece'
W = 1200
GOLD = '#f2d08b'
CREAM = '#fff2d0'


def serif(size):
    return ImageFont.truetype('DejaVuSerif-Bold.ttf', size)


def sans(size):
    return ImageFont.truetype('DejaVuSans.ttf', size)


def tracking(draw, xy, value, font, fill, spacing=4):
    x, y = xy
    for char in value:
        draw.text((x, y), char, font=font, fill=fill)
        x += draw.textlength(char, font=font) + spacing


def scene(name, size, opacity=175):
    im = ImageOps.fit(Image.open(ART/name).convert('RGB'), size, method=Image.Resampling.LANCZOS).convert('RGBA')
    shade = Image.new('RGBA', size)
    d = ImageDraw.Draw(shade)
    for x in range(size[0]):
        alpha = int(opacity * max(.16, 1-x/(size[0]*.82)))
        d.line((x, 0, x, size[1]), fill=(3, 13, 30, alpha))
    return Image.alpha_composite(im, shade)


def frame(draw, height):
    draw.rectangle((13, 13, W-14, height-14), outline=(241, 202, 130, 180), width=2)
    draw.line((30, 29, 115, 29), fill=GOLD, width=3)
    draw.line((W-115, height-30, W-30, height-30), fill=GOLD, width=3)


def save(image, filename):
    image.convert('RGB').save(ART/filename, quality=91, subsampling=0, optimize=True)


def make_log():
    im = scene('harbor-divider.jpg', (W, 390), 210)
    captain = Image.open(ART/'captain-map.png').convert('RGBA')
    captain.thumbnail((410, 545), Image.Resampling.LANCZOS)
    # Preserve proportions; crop only below the waist, never the face or map.
    im.alpha_composite(captain, (760, 5))
    d = ImageDraw.Draw(im)
    frame(d, 390)
    tracking(d, (55, 72), '01  /  THE CAPTAIN’S LOG', sans(17), GOLD, 3)
    d.text((52, 123), 'Ideas into', font=serif(66), fill=CREAM, stroke_width=1, stroke_fill='#332211')
    d.text((52, 201), 'adventures.', font=serif(66), fill=CREAM, stroke_width=1, stroke_fill='#332211')
    d.line((56, 304, 495, 304), fill=GOLD, width=2)
    tracking(d, (58, 319), 'CODE  /  CREATIVITY  /  CURIOSITY', sans(13), '#ecdfc8', 1)
    save(im, 'captains-log.jpg')


def make_record():
    im = Image.new('RGBA', (W, 390), '#0a1b2b')
    d = ImageDraw.Draw(im)
    for x in range(W):
        c = int(12 + 13*x/W)
        d.line((x, 0, x, 390), fill=(c, 37+c//3, 49+c//2, 255))
    for x in range(420, 1200, 100):
        d.arc((x, 30, x+210, 260), 210, 345, fill=(56, 102, 102, 110), width=1)
    poster = Image.open(ART/'wanted-poster.jpg').convert('RGBA')
    poster.thumbnail((240, 344), Image.Resampling.LANCZOS)
    im.alpha_composite(poster, (66, (390-poster.height)//2))
    d = ImageDraw.Draw(im)
    frame(d, 390)
    tracking(d, (370, 75), '02  /  WORLD GOVERNMENT', sans(17), GOLD, 3)
    d.text((366, 130), 'The public', font=serif(64), fill=CREAM)
    d.text((366, 206), 'record.', font=serif(64), fill=CREAM)
    d.line((372, 302, 835, 302), fill=GOLD, width=2)
    tracking(d, (373, 320), 'THE BOUNTY IS FICTIONAL', sans(15), '#a9d7d3', 2)
    save(im, 'public-record.jpg')


def make_footer():
    im = scene('footer-harbor.jpg', (W, 400), 175)
    overlay = Image.new('RGBA', im.size)
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle((440, 75, 1120, 308), 8, fill=(4, 17, 33, 165))
    im = Image.alpha_composite(im, overlay)
    captain = Image.open(ART/'captain-pointing.png').convert('RGBA')
    captain.thumbnail((390, 480), Image.Resampling.LANCZOS)
    im.alpha_composite(captain, (34, 0))
    d = ImageDraw.Draw(im)
    frame(d, 400)
    tracking(d, (480, 108), 'THE NEXT ADVENTURE', sans(17), GOLD, 3)
    d.text((474, 150), 'Join my crew.', font=serif(56), fill=CREAM, stroke_width=1, stroke_fill='#332211')
    d.line((480, 245, 1000, 245), fill=GOLD, width=2)
    tracking(d, (482, 263), 'AI  /  BOTS  /  WEB  /  DESIGN', sans(14), '#f3ead5', 2)
    save(im, 'crew-footer.jpg')


if __name__ == '__main__':
    make_log()
    make_record()
    make_footer()
