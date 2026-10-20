"""Validate README references and generated graphics without network access."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def validate(root=ROOT):
    readme = (root/'README.md').read_text()
    for marker in ['<!-- ACTIVITY:START -->', '<!-- ACTIVITY:END -->']:
        assert readme.count(marker) == 1, 'Activity markers are missing or duplicated'
    assert 'platane/snk' not in readme.lower(), 'Contribution animation belongs to another account'
    assert not re.search(r'<(?:script|iframe|object|embed)\b', readme, re.I), 'Unsupported README embedding'
    for path in re.findall(r'src="(assets/[^"]+)"', readme):
        target = root/path.split("?", 1)[0]
        assert target.is_file(), f'Missing image: {path}'
        assert target.stat().st_size < 2_000_000, f'Image is too large: {path}'
        if target.suffix == '.svg':
            svg = ET.parse(target).getroot()
            assert svg.tag.endswith('svg')
            assert not any(node.tag.endswith(('script', 'foreignObject')) for node in svg.iter())
        else:
            with Image.open(target) as image:
                assert image.width == 1200
                if 'hero' in path:
                    assert image.n_frames > 1, 'Hero must animate'
    print('README references, SVG markup and GIF assets validated')


if __name__ == '__main__':
    validate()
