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

## Edit and preview

1. Edit the prose and project links in `README.md`. Leave the activity comment markers in place.
2. Update colors and the hero drawing in `scripts/profile.py`. Delete `assets/hero.gif` and run the bootstrap command to redraw it.
3. Install `requirements.txt`; the renderer uses Pillow and the DejaVu Sans/Mono fonts included on GitHub's Ubuntu runners.
4. Run:

   ```bash
   python scripts/profile.py --bootstrap
   python -m unittest discover -s tests -v
   python scripts/validate.py
   ```

   Bootstrap creates an honest pending state, without sample statistics. Do not use it to replace live assets unless intentionally resetting them.
5. To regenerate using previously published public data, run `python scripts/profile.py --snapshot assets/activity.json`. Live refresh uses `GH_TOKEN` from the environment; never put a token in the README or a command argument.

The banner is a seamless 4.8-second loop. Text is visible from the first frame; motion stays in the orbital mark and a thin progress accent. The contribution trail is decorative, while cell brightness reflects actual counts. The contribution animation starts expanded; visitors can collapse it. Alt text and ordinary Markdown preserve the profile's content if an image or animation cannot load.

GitHub applies its own Markdown layout and does not support a custom live JavaScript application inside a README. The design therefore uses standard images, links, a table and a details element, with no claim of embedded app-style interactivity.

References: [GitHub workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows), [GITHUB_TOKEN](https://docs.github.com/en/actions/concepts/security/github_token), [GraphQL user contributions](https://docs.github.com/en/graphql/reference/users).
