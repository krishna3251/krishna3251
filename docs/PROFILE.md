# Profile maintenance

The README is a GitHub-native profile with a custom animated GIF banner, readable project links, a public-activity dashboard, and an animated trail over this account's contribution calendar. The GIF files work as image embeds without JavaScript, iframes, external rendering APIs or a personal access token.

## What updates

`.github/workflows/profile.yml` runs at minute 17 each hour, when profile source changes reach `main`, or from **Actions → Profile refresh → Run workflow**. Pull requests validate the code and make a read-only live API check; only default-branch runs publish generated files.

The workflow queries GitHub's GraphQL API using its built-in `GITHUB_TOKEN`:

- Public repositories owned by `krishna3251`, including forks; all result pages are fetched.
- Stars on those public repositories, including forks.
- Primary languages of owned non-fork repositories. These counts describe repositories, not code volume or skill proficiency.
- Four recently pushed, non-archived public repositories, excluding the profile repository itself. A push timestamp can represent someone else's push to a shared repository; this is not presented as a personal commit feed.
- The account's contribution calendar over GitHub's default past-year window. The token does not gain access to private repositories. GitHub may include anonymous private-contribution totals when the account chooses to display them, without repository names or private content.

The activity panel and snapshot show the last successful UTC refresh time. The README's workflow badge links to current run status. Generated asset links include a content fingerprint to reduce stale-image caching. Updates are **hourly snapshots, not instant streaming**: GitHub may delay scheduled jobs, API data and cached images. If a refresh fails, it does not push incomplete results; the previous published assets and their original timestamp remain visible. Scheduled public-repository workflows can be disabled by GitHub after 60 days without repository activity; the Actions page provides the manual run/re-enable controls.

Only the publishing job requests `contents: write`. There are no added secrets and no `pull_request_target` execution. Actions are pinned to commit SHAs. Generated bot commits do not recursively trigger new push workflows. A concurrent manual edit causes a safe rebase or a failed push, never a force-push.

## Artwork and design

The supplied One Piece-inspired artwork lives in `assets/one-piece/`. The five opaque PNG attachments were converted once to high-quality JPEG; the two character PNGs retain their original transparency. The wanted-poster bounty is fictional. The original illustrations are not generated or recolored by the refresh workflow.

`assets/hero.gif` is composed by `hero()` in `scripts/profile.py` from `hero-ocean.jpg`. Its first frame contains the full title and role. Only a few decorative lights pulse; the ship itself does not move. It is committed once and is not re-encoded by hourly refreshes. To rebuild it after changing the artwork or hero code, remove `assets/hero.gif`, then run `python scripts/profile.py --snapshot assets/activity.json`. Inspect and commit the rebuilt GIF. Keep it below 2 MB.

The Captain’s Log panel combines `harbor-divider.jpg` with `captain-map.png`, the public-record panel includes `wanted-poster.jpg`, and the footer combines `footer-harbor.jpg` with `captain-pointing.png`. After changing these sources or the compositing code, regenerate the three panels with `python scripts/artwork.py`, then review and commit the resulting JPEGs. The original character PNGs remain transparent. The fruit illustration is a self-contained static SVG, so it does not rely on SVG animation surviving GitHub sanitization. Important technologies, project descriptions and contact links also appear as text in the README.

The sea chart uses each returned calendar day and its weekday, with a date range and total. Colors are computed from counts (0, 1, 2–3, 4–7, and 8+), not animated. The moving outlines are decorative and do not change cell fills. The chart is a compact visualization rather than GitHub's interactive per-day calendar; follow the image link to the account for the native calendar and per-day details. The dashboard lists the top five languages; the complete non-fork language distribution appears in the generated Markdown immediately below it.

## Edit and preview

1. Edit the prose and links in `README.md`. Keep both activity markers exactly once and in order.
2. Install `requirements.txt`; rendering uses Pillow and DejaVu fonts available on GitHub's Ubuntu runners.
3. Regenerate from the last published snapshot without replacing real data with a pending state:

   ```bash
   python scripts/profile.py --snapshot assets/activity.json
   python -m unittest discover -s tests -v
   python scripts/validate.py
   ```

4. `python scripts/profile.py --bootstrap` creates honest pending graphics and must not be used to replace live assets unless intentionally resetting them. Live refresh uses `GH_TOKEN` from the environment; never put a token in the README or command arguments. A snapshot with another account's login is rejected.
5. Open the branch README on GitHub to inspect GitHub's rendering at desktop and phone widths. GIFs work as image embeds; static first frames remain readable if animation stops. GitHub may cache images, which is why generated activity links include fingerprints. Light and dark mode use the same opaque navy graphics with Markdown text adapting to GitHub's theme.

GitHub does not support a custom live JavaScript application inside a README. This profile uses ordinary Markdown, links and locally hosted images, without iframes, external rendering services or assumptions about SVG animation.

References: [GitHub workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows), [GITHUB_TOKEN](https://docs.github.com/en/actions/concepts/security/github_token), [GraphQL user contributions](https://docs.github.com/en/graphql/reference/users).
