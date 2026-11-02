"""Validate README assets and generated graphics without network access."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ART = {
    'hero-ocean.jpg': (2048, 682), 'harbor-divider.jpg': (2048, 682),
    'footer-harbor.jpg': (2048, 682), 'project-fleet.jpg': (1672, 941),
    'wanted-poster.jpg': (1055, 1491), 'captain-map.png': (1086, 1448),
    'captain-pointing.png': (1122, 1402), 'crew-footer.jpg': (1200, 400),
}


def validate(root=ROOT):
    readme = (root/'README.md').read_text(encoding='utf-8')
    markers = ['<!-- ACTIVITY:START -->', '<!-- ACTIVITY:END -->']
    for marker in markers:
        assert readme.count(marker) == 1, 'Activity markers are missing or duplicated'
    assert readme.index(markers[0]) < readme.index(markers[1]), 'Activity markers are out of order'
    assert 'platane/snk' not in readme.lower(), 'Contribution animation belongs to another account'
    assert not re.search(r'<(?:script|iframe|object|embed|video)\b', readme, re.I), 'Unsupported README embedding'
    assert not re.search(r'\son\w+\s*=|\sstyle\s*=', readme, re.I), 'Unsupported inline behavior or style'
    paths = set(re.findall(r'src="(assets/[^"]+)"', readme))
    assert paths, 'README has no local images'
    for path in paths:
        target = root/path.split('?', 1)[0]
        assert target.is_file(), f'Missing image: {path}'
        assert target.stat().st_size < 2_000_000, f'Image is too large: {path}'
        if target.suffix == '.svg':
            svg = ET.parse(target).getroot()
            assert svg.tag.endswith('svg')
            for node in svg.iter():
                assert not node.tag.endswith(('script', 'foreignObject')), 'Unsafe SVG element'
                assert not any(k.lower().startswith('on') for k in node.attrib), 'Unsafe SVG handler'
        else:
            with Image.open(target) as image:
                image.verify()
            with Image.open(target) as image:
                if target.name == 'hero.gif':
                    assert image.size == (1200, 410) and image.n_frames > 1, 'Invalid hero animation'
                if target.name == 'contributions.gif':
                    assert image.size == (1200, 265), 'Invalid calendar dimensions'
    for name, size in REQUIRED_ART.items():
        target = root/'assets/one-piece'/name
        assert target.is_file() and target.stat().st_size < 2_000_000, f'Missing or oversized source: {name}'
        with Image.open(target) as image:
            assert image.size == size, f'Unexpected dimensions: {name}'
            if name.startswith('captain-'):
                assert image.mode == 'RGBA' and image.getchannel('A').getextrema() == (0, 255), f'Transparency missing: {name}'
    print('README references, artwork, SVG markup and GIF assets validated')


if __name__ == '__main__':
    validate()
