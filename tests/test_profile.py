import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops

SPEC = importlib.util.spec_from_file_location('profile_renderer', Path(__file__).resolve().parents[1]/'scripts/profile.py')
profile = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(profile)


def repo(name, *, fork=False, language='Python', archived=False):
    return {'name': name, 'nameWithOwner': f'krishna3251/{name}', 'url': f'https://github.com/krishna3251/{name}',
            'isFork': fork, 'isArchived': archived, 'stargazerCount': 2,
            'primaryLanguage': {'name': language} if language else None, 'pushedAt': '2026-10-20T07:10:00Z'}


def snapshot():
    return {'login': profile.USER, 'updated_at': '2026-10-20 07:10 UTC',
            'repositories': [repo('example'), repo('forked', fork=True, language='JavaScript')],
            'calendar': {'totalContributions': 7, 'weeks': [{'contributionDays': [
                {'date': f'2026-10-{18+i}', 'weekday': i, 'contributionCount': i} for i in range(3)
            ]}]}}


def response(nodes, more=False, cursor=None, login=profile.USER):
    data = {'data': {'user': {'login': login, 'repositories': {'nodes': nodes,
            'pageInfo': {'hasNextPage': more, 'endCursor': cursor}},
            'contributionsCollection': {'contributionCalendar': snapshot()['calendar']}}}}
    return io.BytesIO(json.dumps(data).encode())


class DataTests(unittest.TestCase):
    def test_all_public_repository_pages_are_fetched_and_deduplicated(self):
        opener = Mock(side_effect=[response([repo('one')], True, 'cursor1'), response([repo('one'), repo('two')])])
        data = profile.get_profile('synthetic-token', opener)
        self.assertEqual(len(data['repositories']), 2)
        second_request = opener.call_args_list[1].args[0]
        self.assertEqual(json.loads(second_request.data)['variables']['cursor'], 'cursor1')
        self.assertIn('privacy: PUBLIC', json.loads(second_request.data)['query'])

    def test_api_errors_do_not_become_zeroed_statistics(self):
        opener = Mock(return_value=io.BytesIO(b'{"errors":[{"message":"unavailable"}]}'))
        with self.assertRaises(RuntimeError):
            profile.get_profile('synthetic-token', opener)

    def test_wrong_account_and_nonadvancing_pagination_are_rejected(self):
        for first, second in [(response([], login='someone-else'), None),
                              (response([], True, 'same'), response([], True, 'same'))]:
            opener = Mock(side_effect=[first, second])
            with self.assertRaises(RuntimeError):
                profile.get_profile('synthetic-token', opener)

    def test_rendered_metrics_distinguish_repo_languages_from_skill_claims(self):
        svg = profile.activity_svg(snapshot())
        ET.fromstring(svg)
        self.assertIn('Python · 1', svg)
        self.assertNotIn('JavaScript · 1', svg)  # fork excluded from language counts
        self.assertIn('2026-10-20 07:10 UTC', svg)
        self.assertIn('PUBLIC REPOSITORIES', svg)

    def test_activity_excludes_profile_and_archived_repos_and_escapes_markup(self):
        data = snapshot()
        data['repositories'] += [repo(profile.USER), repo('archived', archived=True)]
        output = profile.activity_markdown(data)
        self.assertNotIn('archived', output)
        self.assertNotIn(f'](https://github.com/{profile.USER}/{profile.USER})', output)
        self.assertIn('Latest push', output)
        self.assertIn(r'\[x\]', profile.markdown_label('[x]'))
        data['repositories'] = [repo('../unsafe')]
        with self.assertRaises(ValueError):
            profile.activity_markdown(data)

    def test_markers_preserve_surrounding_readme_and_fail_on_ambiguity(self):
        original = 'intro\n<!-- ACTIVITY:START -->old<!-- ACTIVITY:END -->\nfooter'
        changed = profile.update_readme(original, 'new')
        self.assertEqual(changed, 'intro\n<!-- ACTIVITY:START -->\nnew\n<!-- ACTIVITY:END -->\nfooter')
        for value in ['', '<!-- ACTIVITY:END --><!-- ACTIVITY:START -->', original+'<!-- ACTIVITY:START -->']:
            with self.assertRaises(ValueError):
                profile.update_readme(value, 'new')

    def test_svg_escapes_repository_language_markup(self):
        data = snapshot()
        data['repositories'][0]['primaryLanguage']['name'] = '<script>alert(1)</script>'
        svg = profile.activity_svg(data)
        ET.fromstring(svg)
        self.assertNotIn('<script>', svg)


class GraphicsTests(unittest.TestCase):
    def test_hero_animates_and_every_frame_stays_under_asset_budget(self):
        root = Path(__file__).resolve().parents[1]
        with Image.open(root/'assets/hero.gif') as image:
            self.assertGreater(image.n_frames, 1)  # GIF encoding may merge identical frames
            first = image.convert('RGB')
            image.seek(12)
            self.assertIsNotNone(ImageChops.difference(first, image.convert('RGB')).getbbox())
            self.assertEqual(image.size, (1200,410))
        self.assertLess((root/'assets/hero.gif').stat().st_size, 2_000_000)

    def test_contribution_animation_uses_account_counts_and_preserves_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'README.md').write_text('<img src="assets/activity.svg" /><img src="assets/contributions.gif" /><!-- ACTIVITY:START -->\n<!-- ACTIVITY:END -->')
            (root/'assets').mkdir()
            # Reuse the static hero; hourly runs must not re-encode it.
            (root/'assets/hero.gif').write_bytes(b'preserve-hero')
            data = snapshot()
            profile.render(data, output=root)
            self.assertEqual((root/'assets/hero.gif').read_bytes(), b'preserve-hero')
            self.assertEqual(json.loads((root/'assets/activity.json').read_text()), data)
            with Image.open(root/'assets/contributions.gif') as image:
                self.assertGreater(image.n_frames, 1)
                self.assertEqual(image.size, (1200,265))
            self.assertIn(data['updated_at'], (root/'README.md').read_text())
            self.assertIn('assets/activity.svg?v=', (root/'README.md').read_text())
            self.assertIn('assets/contributions.gif?v=', (root/'README.md').read_text())

    def test_pending_state_does_not_invent_stats(self):
        svg = profile.activity_svg(None)
        self.assertIn('FIRST REFRESH PENDING', svg)
        self.assertNotIn('CONTRIBUTIONS / PAST YEAR', svg)
