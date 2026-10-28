"""Render a self-hosted GitHub profile from public account data.

No personal access token or external badge/image service required.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from html import escape
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BG = '#071525'
PANEL = '#10283a'
LINE = '#2c4c59'
WHITE = '#f8f3e6'
MUTED = '#a9bfc5'
MINT = '#e9c27c'
VIOLET = '#82d9d1'
USER = 'krishna3251'
QUERY = '''query Profile($login: String!, $cursor: String) {
  user(login: $login) {
    login
    repositories(first: 100, after: $cursor, privacy: PUBLIC, ownerAffiliations: OWNER, orderBy: {field: PUSHED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes { name nameWithOwner url isFork isArchived stargazerCount primaryLanguage { name } pushedAt }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday } }
      }
    }
  }
}'''


def get_profile(token, opener=urlopen):
    """GraphQL pagination only includes public, owned repositories."""
    cursor = None
    repos = []
    calendar = None
    while True:
        body = json.dumps({'query': QUERY, 'variables': {'login': USER, 'cursor': cursor}}).encode()
        request = Request('https://api.github.com/graphql', body, {
            'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
            'User-Agent': 'krishna3251-profile-refresh',
        })
        with opener(request, timeout=30) as response:
            result = json.load(response)
        # Do not print provider responses, credentials or private API details.
        if result.get('errors') or not result.get('data', {}).get('user'):
            raise RuntimeError('GitHub did not return the public profile data')
        user = result['data']['user']
        if user['login'].lower() != USER.lower():
            raise RuntimeError('GitHub returned a different profile')
        calendar = user['contributionsCollection']['contributionCalendar']
        connection = user['repositories']
        repos.extend(connection['nodes'])
        if not connection['pageInfo']['hasNextPage']:
            break
        next_cursor = connection['pageInfo']['endCursor']
        if not next_cursor or next_cursor == cursor:
            raise RuntimeError('GitHub pagination did not advance')
        cursor = next_cursor
    unique = {repo['nameWithOwner']: repo for repo in repos}
    return {'login': USER, 'repositories': list(unique.values()), 'calendar': calendar,
            'updated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}


def font(size, bold=False, mono=False):
    name = 'DejaVuSansMono' if mono else 'DejaVuSans'
    suffix = '-Bold' if bold else ''
    return ImageFont.truetype(f'{name}{suffix}.ttf', size)


def rgb(color):
    return tuple(int(color[i:i+2], 16) for i in (1, 3, 5))


def rounded(draw, box, fill=PANEL, radius=18, outline=LINE):
    draw.rounded_rectangle(box, radius, fill=fill, outline=outline, width=1)


def text(draw, xy, value, size=18, fill=WHITE, bold=False, mono=False):
    draw.text(xy, value, font=font(size, bold=bold, mono=mono), fill=fill)


def save_gif(frames, path, duration):
    # Shared palette keeps text and gradients steady across frames.
    palette = frames[0].quantize(colors=128)
    converted = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    converted[0].save(path, save_all=True, append_images=converted[1:], loop=0,
                      duration=duration, optimize=True, disposal=1)


def hero(path):
    """Create a cinematic loop from the committed illustration."""
    base = Image.open(ROOT/'assets/krishna-art.jpg').convert('RGB')
    draw = ImageDraw.Draw(base)
    # A dark text field keeps the lettering readable over the artwork.
    overlay = Image.new('RGBA', base.size, (0, 0, 0, 0))
    shade = ImageDraw.Draw(overlay)
    for x in range(680):
        alpha = int(155 * max(0, 1 - x / 680))
        shade.line((x, 0, x, 410), fill=(2, 9, 23, alpha))
    base = Image.alpha_composite(base.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(base)
    text(draw, (54, 44), 'KRISHNA3251  /  CREATIVE LAB', 15, '#e8c887', mono=True)
    text(draw, (49, 94), 'KRISHNA', 78, '#fff7e8', bold=True)
    draw.line((54, 199, 400, 199), fill='#d5a961', width=2)
    text(draw, (54, 220), 'BUILD WITH PURPOSE.', 25, '#f2d294', bold=True)
    text(draw, (54, 260), 'CREATE WITH IMAGINATION.', 22, '#d3e6ed', bold=True)
    text(draw, (54, 350), 'AI  /  BOTS  /  WEB  /  DESIGN', 14, '#e8c887', mono=True)
    frames = []
    for frame in range(48):
        image = base.copy()
        d = ImageDraw.Draw(image)
        phase = frame / 48 * math.tau
        for x, y, offset in [(80, 314, 0), (252, 320, 1.4), (447, 69, 2.6), (545, 290, 4.1), (660, 85, 5.2)]:
            glow = 0.5 + 0.5 * math.sin(phase + offset)
            color = (int(110 + 145 * glow), int(85 + 115 * glow), int(50 + 75 * glow))
            r = 1 + int(glow > 0.7)
            d.ellipse((x-r, y-r, x+r, y+r), fill=color)
        frames.append(image)
    save_gif(frames, path, 100)


def svg_text(x, y, value, size=18, fill=WHITE, weight=400, extra=''):
    return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}" {extra}>{escape(str(value))}</text>'


def activity_svg(data):
    header = f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="300" viewBox="0 0 1200 300" role="img"><title>Krishna public GitHub activity</title><rect width="1200" height="300" rx="18" fill="{BG}"/><g font-family="DejaVu Sans,Arial,sans-serif">'
    if not data:
        return header + svg_text(40, 78, 'ACTIVITY / FIRST REFRESH PENDING', 18, MINT, 600) + svg_text(40, 139, 'Account data will appear after the first successful workflow run.', 22) + svg_text(40, 200, 'No sample metrics. No borrowed contribution history.', 17, MUTED) + '</g></svg>'
    repos = data['repositories']
    originals = [repo for repo in repos if not repo['isFork']]
    languages = Counter(repo['primaryLanguage']['name'] for repo in originals if repo['primaryLanguage'])
    total = data['calendar']['totalContributions']
    parts = [header, svg_text(36, 41, 'GITHUB / PUBLIC SIGNAL', 16, MINT, 600), svg_text(1164, 41, data['updated_at'], 13, MUTED, extra='text-anchor="end"')]
    metrics = [(len(repos), 'PUBLIC REPOSITORIES'), (sum(r['stargazerCount'] for r in repos), 'STARS ON OWNED REPOS'), (total, 'CONTRIBUTIONS / PAST YEAR')]
    for index, (number, label) in enumerate(metrics):
        left = 36 + index*385
        parts += [f'<rect x="{left}" y="65" width="358" height="122" rx="12" fill="{PANEL}" stroke="{LINE}"/>', svg_text(left+20, 122, f'{number:,}', 42, WHITE, 700), svg_text(left+20, 157, label, 12, MUTED)]
    parts.append(svg_text(36, 222, 'REPOSITORY LANGUAGES', 12, MUTED, 600))
    parts.append(svg_text(36, 259, '  /  '.join(f'{language} · {count}' for language, count in languages.most_common(5)) or 'No primary language data yet', 18, VIOLET))
    return ''.join(parts) + '</g></svg>'


def contributions(data, path):
    width, height = 1200, 265
    base = Image.new('RGB', (width, height), BG)
    d = ImageDraw.Draw(base)
    text(d, (35, 22), 'A YEAR OF BUILDING', 18, MINT, bold=True, mono=True)
    if not data:
        text(d, (35, 98), 'Waiting for your first GitHub Actions refresh.', 27)
        text(d, (35, 154), 'Your account. Your contributions. No invented activity.', 18, MUTED)
        base.save(path, format='GIF')
        return
    calendar = data['calendar']
    weeks = calendar['weeks']
    text(d, (35, 227), f"{calendar['totalContributions']:,} contributions in the past year", 15, MUTED)
    text(d, (885, 227), 'KRISHNA3251 / GITHUB', 13, MUTED, mono=True)
    colors = ['#182b3b', '#31514f', '#567c69', '#b2925a', MINT]
    coordinates = []
    for week_index, week in enumerate(weeks):
        for day in week['contributionDays']:
            x, y = 36+week_index*21, 69+day['weekday']*20
            count = day['contributionCount']
            level = 0 if not count else min(4, 1+int(math.log2(count)))
            d.rounded_rectangle((x,y,x+15,y+14), 3, fill=colors[level])
            coordinates.append((x, y))
    frames = []
    # A decorative scanning trail; data cells remain untouched underneath it.
    for frame in range(56):
        image = base.copy()
        draw = ImageDraw.Draw(image)
        head = int(frame/56*len(coordinates))
        for step in range(8):
            x,y = coordinates[(head-step) % len(coordinates)]
            if step == 0:
                draw.rounded_rectangle((x-1,y-1,x+16,y+15), 4, outline=WHITE, width=2)
            else:
                draw.rounded_rectangle((x,y,x+15,y+14), 3, outline=VIOLET, width=1)
        frames.append(image)
    save_gif(frames, path, 100)


def markdown_label(value):
    # Only generated repository names enter Markdown, never event payload text.
    return re.sub(r'([\\`*{}_\[\]<>|])', r'\\\1', value)


def activity_markdown(data):
    repos = sorted((r for r in data['repositories'] if r['pushedAt'] and not r['isArchived'] and r['name'] != USER), key=lambda r:r['pushedAt'], reverse=True)[:4]
    lines = [f"<sub>Last successful refresh: **{data['updated_at']}** · hourly + profile updates · public data only</sub>", '', '| Recently pushed repository | Latest push · UTC |', '| :--- | :--- |']
    for repo in repos:
        # URLs are constructed from GitHub identifiers, not arbitrary API URLs.
        target = repo['nameWithOwner']
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', target):
            raise ValueError('Invalid GitHub repository identifier')
        lines.append(f"| [{markdown_label(repo['name'])}](https://github.com/{target}) | {repo['pushedAt'][:16].replace('T', ' · ')} |")
    if not repos:
        lines.append('| No public pushes available yet | — |')
    return '\n'.join(lines)


def update_readme(content, generated):
    start, end = '<!-- ACTIVITY:START -->', '<!-- ACTIVITY:END -->'
    if content.count(start) != 1 or content.count(end) != 1 or content.index(start) > content.index(end):
        raise ValueError('README activity markers must appear once in order')
    prefix, remaining = content.split(start)
    _, suffix = remaining.split(end)
    return prefix + start + '\n' + generated + '\n' + end + suffix


def render(data=None, output=ROOT):
    assets = output/'assets'
    assets.mkdir(parents=True, exist_ok=True)
    # Hero is data-independent and committed once, not re-encoded every hour.
    if not (assets/'hero.gif').exists():
        hero(assets/'hero.gif')
    (assets/'activity.svg').write_text(activity_svg(data), encoding='utf-8')
    contributions(data, assets/'contributions.gif')
    if data:
        (assets/'activity.json').write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
        readme = output/'README.md'
        content = update_readme(readme.read_text(), activity_markdown(data))
        for filename in ['activity.svg', 'contributions.gif']:
            fingerprint = hashlib.sha256((assets/filename).read_bytes()).hexdigest()[:12]
            pattern = rf'src="assets/{re.escape(filename)}(?:\?v=[a-f0-9]+)?"'
            content = re.sub(pattern, f'src="assets/{filename}?v={fingerprint}"', content)
        readme.write_text(content, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bootstrap', action='store_true', help='Render honest pending-state assets without an API token')
    parser.add_argument('--snapshot', type=Path, help='Render an existing public-data snapshot')
    args = parser.parse_args()
    if args.bootstrap:
        data = None
    elif args.snapshot:
        data = json.loads(args.snapshot.read_text())
    else:
        token = os.getenv('GH_TOKEN', '')
        if not token:
            raise RuntimeError('GH_TOKEN is required for live refresh')
        data = get_profile(token)
    render(data)
    print('Profile assets generated' if not data else f"Public profile refreshed: {data['updated_at']}")


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Profile refresh failed ({type(error).__name__}); previous published assets remain unchanged.', file=sys.stderr)
        sys.exit(1)
